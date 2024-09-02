from flask import Flask, redirect, url_for, session, request, jsonify
from flask_session import Session
from msal import ConfidentialClientApplication
from models.user_model import User
from models.audit_model import AuditTrail
import uuid
from app import db

app = Flask(__name__)
Session(app)

@app.route('/login')
def login():
    client_app = ConfidentialClientApplication(
        app.config['CLIENT_ID'],
        authority=app.config['AUTHORITY'],
        client_credential=app.config['CLIENT_SECRET']
    )
    auth_url = client_app.get_authorization_request_url(
        app.config['SCOPE'],
        state=str(uuid.uuid4()),
        redirect_uri=url_for('auth_callback', _external=True)
    )
    return redirect(auth_url)

@app.route(app.config['REDIRECT_PATH'])
def auth_callback():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for('index'))  # Prevent CSRF
    if 'error' in request.args:
        return "Login failed: " + request.args['error']
    if request.args.get('code'):
        cache = load_cache()
        client_app = ConfidentialClientApplication(
            app.config['CLIENT_ID'], authority=app.config['AUTHORITY'],
            client_credential=app.config['CLIENT_SECRET'], token_cache=cache)
        result = client_app.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=app.config['SCOPE'],
            redirect_uri=url_for('auth_callback', _external=True))

        if "error" in result:
            return "Authentication failed: " + result["error_description"]

        session['user'] = result.get('id_token_claims')
        save_cache(cache)

        # Log successful login to audit trail
        user_email = session['user'].get('preferred_username')
        user = User.query.filter_by(email=user_email).first()
        if user:
            audit = AuditTrail(
                user_id=user.id,
                action='LOGIN',
                resource_type='user',
                resource_id=user.id,
                details=f"User {user_email} logged in."
            )
            db.session.add(audit)
            db.session.commit()

        return redirect(url_for('authorized'))

@app.route('/logout')
def logout():
    user_email = session.get('user', {}).get('preferred_username')
    user = User.query.filter_by(email=user_email).first()
    if user:
        # Log successful logout to audit trail
        audit = AuditTrail(
            user_id=user.id,
            action='LOGOUT',
            resource_type='user',
            resource_id=user.id,
            details=f"User {user_email} logged out."
        )
        db.session.add(audit)
        db.session.commit()

    session.clear()
    return redirect(url_for('index'))

def load_cache():
    return msal.SerializableTokenCache()

def save_cache(cache):
    if cache.has_state_changed:
        # Implement saving the cache to a persistent storage (e.g., database)
        pass

@app.route('/authorized')
def authorized():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_email = session['user'].get('preferred_username')
    # Check if the user email is in the approved list (in the database)
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return "Access Denied", 403

    return "You are logged in as: " + user_email
