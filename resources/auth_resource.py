from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from models.user_model import User
from models.user_session_model import UserSession
from models.audit_model import AuditTrail
from models.token_model import TokenBlacklist, RefreshToken
from app import db, logger
from werkzeug.security import check_password_hash

# Define a namespace for auth-related operations
auth_ns = Namespace('auth', description='Authentication operations')

# Define models for Swagger documentation
login_model = auth_ns.model('LoginResponse', {
    'message': fields.String(description='Login message'),
    'access_token': fields.String(description='JWT Access Token'),
    'refresh_token': fields.String(description='JWT Refresh Token'),
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

# Authentication resource class for login
@auth_ns.route('/login')
class LoginResource(Resource):
    @auth_ns.expect(auth_ns.model('LoginCredentials', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password'),
        'ip_address': fields.String(required=True, description='User IP address')  # Capture IP address
    }), validate=True)
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Login user and return JWT access and refresh tokens."""
        data = request.json
        email = data.get('email')
        password = data.get('password')
        ip_address = data.get('ip_address')

        # Fetch user by email
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed login attempt for email {email}.")
            return {'message': 'Invalid credentials'}, 401

        # Create JWT tokens
        access_token = create_access_token(identity={'id': user.id, 'email': user.email, 'role': user.role.name})
        refresh_token = create_refresh_token(identity={'id': user.id, 'email': user.email, 'role': user.role.name})

        # Track user session
        if not UserSession.validate_ip(ip_address):
            logger.error(f"Invalid IP address {ip_address} provided.")
            return {'message': 'Invalid IP address'}, 400

        session = UserSession(user_id=user.id, ip_address=ip_address)
        db.session.add(session)
        db.session.commit()

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

        logger.info(f"User {user.email} logged in successfully.")
        return {
            'message': 'Logged in successfully',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.serialize()
        }, 200


# Refresh token endpoint
@auth_ns.route('/refresh')
class RefreshTokenResource(Resource):
    @auth_ns.doc(description='Use the refresh token to get a new access token.')
    @auth_ns.response(200, 'Success', model=login_model)
    @jwt_required(refresh=True)  # Ensure this endpoint only accepts refresh tokens
    def post(self):
        """Generate a new access token using a valid refresh token."""
        current_user = get_jwt_identity()

        # Create new access token
        access_token = create_access_token(identity=current_user)

        logger.info(f"User {current_user['email']} refreshed their access token.")
        return {
            'message': 'Access token refreshed successfully',
            'access_token': access_token
        }, 200


# Logout resource class
@auth_ns.route('/logout')
class LogoutResource(Resource):
    @auth_ns.doc(description='Logs the user out and invalidates the JWT token.')
    @auth_ns.response(200, 'Success', model=logout_model)
    @jwt_required()
    def post(self):
        """Logout user by blacklisting the JWT token and ending session."""
        current_user = get_jwt_identity()

        # Blacklist the JWT token
        jti = get_jwt()['jti']  # JWT ID (unique identifier for the token)
        token_blacklist = TokenBlacklist(jti=jti, user_id=current_user['id'], token_type='access', revoked=True)
        db.session.add(token_blacklist)

        # End active user session
        active_sessions = UserSession.get_active_sessions(current_user['id'])
        for session in active_sessions:
            session.end_session()

        # Log logout event to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='LOGOUT',
            resource_type='user',
            resource_id=current_user['id'],
            details=f"User {current_user['email']} logged out"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"User {current_user['email']} logged out successfully.")
        return {'message': 'Logged out successfully'}, 200


# Blacklist refresh token on logout
@auth_ns.route('/revoke_refresh')
class RevokeRefreshTokenResource(Resource):
    @auth_ns.doc(description='Revoke a refresh token explicitly.')
    @auth_ns.response(200, 'Success', model=logout_model)
    @jwt_required(refresh=True)  # Ensure this endpoint only accepts refresh tokens
    def post(self):
        """Revoke the refresh token upon user logout."""
        current_user = get_jwt_identity()

        jti = get_jwt()['jti']  # JWT ID for refresh token
        refresh_token = RefreshToken.query.filter_by(token=jti, user_id=current_user['id'], revoked=False).first()

        if not refresh_token:
            return {'message': 'Refresh token not found or already revoked'}, 404

        # Revoke the refresh token
        refresh_token.revoke()

        # Log refresh token revocation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='REVOKE_REFRESH_TOKEN',
            resource_type='refresh_token',
            resource_id=refresh_token.id,
            details=f"User revoked refresh token with ID {refresh_token.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"User {current_user['email']} revoked refresh token {refresh_token.id}.")
        return {'message': 'Refresh token revoked successfully'}, 200
