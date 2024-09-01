from flask_restful import Resource
from flask import request, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from models.user_model import User
from models.audit_model import AuditTrail
from app import db

# Initialize OAuth
oauth = OAuth()
oauth.register(
    name='microsoft',
    client_id='your_client_id',
    client_secret='your_client_secret',
    authorize_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    authorize_params=None,
    access_token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token',
    access_token_params=None,
    refresh_token_url=None,
    client_kwargs={'scope': 'openid email profile'},
)

class AuthResource(Resource):
    def get(self):
        redirect_uri = url_for('authcallbackresource', _external=True)
        return oauth.microsoft.authorize_redirect(redirect_uri)

class AuthCallbackResource(Resource):
    def get(self):
        token = oauth.microsoft.authorize_access_token()
        user_info = oauth.microsoft.parse_id_token(token)

        # Check if user exists in the database
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            return {"message": "Unauthorized. User not found."}, 403

        # Set session information
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_role'] = user.role.name

        # Log login event to audit trail
        audit = AuditTrail(
            user_id=user.id,
            action='LOGIN',
            resource_type='user',
            resource_id=user.id,
            details=f"User {user.email} logged in"
        )
        db.session.add(audit)
        db.session.commit()

        return {"message": "Logged in successfully", "user": user.serialize()}

class LogoutResource(Resource):
    def get(self):
        user_id = session.get('user_id')
        user_email = session.get('user_email')

        # Log logout event to audit trail if user is in session
        if user_id:
            audit = AuditTrail(
                user_id=user_id,
                action='LOGOUT',
                resource_type='user',
                resource_id=user_id,
                details=f"User {user_email} logged out"
            )
            db.session.add(audit)
            db.session.commit()

        session.clear()
        return {"message": "Logged out successfully"}
