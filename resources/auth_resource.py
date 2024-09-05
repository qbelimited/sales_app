from flask_restx import Namespace, Resource, fields
from flask import request, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from models.user_model import User
from models.audit_model import AuditTrail
from app import db
import os

# Define a namespace for auth-related operations
auth_ns = Namespace('auth', description='Authentication operations')

# Define models for Swagger documentation
login_model = auth_ns.model('LoginResponse', {
    'message': fields.String(description='Login message'),
    'user': fields.Nested(auth_ns.model('User', {
        'id': fields.Integer(description='User ID'),
        'email': fields.String(description='User email'),
        'name': fields.String(description='User name'),
        'role_id': fields.Integer(description='Role ID'),
    }))
})

logout_model = auth_ns.model('LogoutResponse', {
    'message': fields.String(description='Logout message')
})

# Authentication resource class
@auth_ns.route('/login')
class AuthResource(Resource):
    @auth_ns.doc(description='Initiates Microsoft OAuth login.')
    def get(self):
        """Initiate OAuth login with Microsoft."""
        redirect_uri = url_for('authcallbackresource', _external=True)
        return oauth.microsoft.authorize_redirect(redirect_uri)

@auth_ns.route('/callback')
class AuthCallbackResource(Resource):
    @auth_ns.doc(description='Handles the OAuth callback from Microsoft and logs the user in.')
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(403, 'Unauthorized')
    def get(self):
        """Handle Microsoft OAuth callback and login the user."""
        try:
            # Retrieve the token from the callback
            token = oauth.microsoft.authorize_access_token()
            user_info = oauth.microsoft.parse_id_token(token)
        except Exception as e:
            return {"message": "OAuth error: Could not retrieve user information", "error": str(e)}, 400

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

        return {"message": "Logged in successfully", "user": user.serialize()}, 200

@auth_ns.route('/logout')
class LogoutResource(Resource):
    @auth_ns.doc(description='Logs the user out and clears the session.')
    @auth_ns.response(200, 'Success', model=logout_model)
    def get(self):
        """Logs out the user and clears the session."""
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
        return {"message": "Logged out successfully"}, 200

