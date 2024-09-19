from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt, decode_token
)
from jwt.exceptions import ExpiredSignatureError
from models.user_model import User
from models.user_session_model import UserSession
from models.audit_model import AuditTrail
from models.token_model import TokenBlacklist, RefreshToken
from app import db, logger
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta

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

# Utility function to check admin privileges
def is_admin():
    current_user = get_jwt_identity()
    return current_user.get('role') == 'admin'

# Authentication resource class for login
@auth_ns.route('/login')
class LoginResource(Resource):
    @auth_ns.expect(auth_ns.model('LoginCredentials', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password')
    }), validate=True)
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Login user and return JWT access and refresh tokens."""
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"Failed login attempt for email {email}.")
            return {'message': 'Invalid credentials'}, 401

        ip_address = request.remote_addr

        if not UserSession.validate_ip(ip_address):
            logger.error(f"Invalid IP address {ip_address} provided.")
            return {'message': 'Invalid IP address'}, 400

        # Revoke old refresh tokens to prevent reuse
        old_refresh_token = RefreshToken.query.filter_by(user_id=user.id, revoked=False).first()
        if old_refresh_token:
            old_refresh_token.revoke()
            logger.info(f"Old refresh token for user {user.email} revoked.")

        # Set access and refresh token expiration times
        access_token_expiry = timedelta(hours=1)
        refresh_token_expiry = timedelta(hours=12)

        access_token = create_access_token(identity={'id': user.id, 'email': user.email, 'role': user.role.name}, expires_delta=access_token_expiry)
        refresh_token = create_refresh_token(identity={'id': user.id, 'email': user.email, 'role': user.role.name}, expires_delta=refresh_token_expiry)

        session_expiry = datetime.utcnow() + access_token_expiry
        session = UserSession(user_id=user.id, ip_address=ip_address, expires_at=session_expiry)
        db.session.add(session)

        refresh_token_record = RefreshToken(user_id=user.id, token=refresh_token, expire_at=datetime.utcnow() + refresh_token_expiry)
        db.session.add(refresh_token_record)
        db.session.commit()

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
            'expiry': access_token_expiry.total_seconds(),
            'user': user.serialize()
        }, 200


# Refresh token endpoint
@auth_ns.route('/refresh')
class RefreshTokenResource(Resource):
    @auth_ns.doc(description='Use the refresh token to get a new access token.')
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(401, 'Invalid or expired refresh token')
    @jwt_required(refresh=True)  # Ensure this endpoint only accepts refresh tokens
    def post(self):
        """Generate a new access token using a valid refresh token."""
        try:
            current_user = get_jwt_identity()

            # Check if the refresh token has expired
            jti_refresh = get_jwt()['jti']
            refresh_token_record = RefreshToken.query.filter_by(token=jti_refresh, user_id=current_user['id'], revoked=False).first()

            if not refresh_token_record or refresh_token_record.expire_at < datetime.utcnow():
                logger.error(f"Refresh token for user {current_user['email']} has expired or been revoked.")
                return {'message': 'Refresh token has expired or been revoked.'}, 401

            # Create a new access token with 1-hour expiration
            access_token = create_access_token(
                identity=current_user,
                expires_delta=timedelta(hours=1)
            )

            logger.info(f"User {current_user['email']} refreshed their access token.")

            audit = AuditTrail(
                user_id=current_user['id'],
                action='LOGIN',
                resource_type='user',
                resource_id=current_user['id'],
                details=f"User {current_user['email']} token refreshed successfully"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'message': 'Access token refreshed successfully',
                'access_token': access_token,
                'expiry': timedelta(hours=1).total_seconds(),
                'user': current_user
            }, 200

        except ExpiredSignatureError:
            logger.error("Attempted refresh with an expired token.")
            return {'message': 'The refresh token has expired. Please log in again.'}, 401
        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}")
            db.session.rollback()
            return {'message': 'An error occurred during token refresh. Please try again.'}, 500

# Logout resource class with enhanced refresh token revocation, user sessions update and blacklist handling
@auth_ns.route('/logout')
class LogoutResource(Resource):
    @auth_ns.doc(description='Logs the user out by revoking the refresh token and optionally blacklisting the access token.')
    @auth_ns.response(200, 'Success', model=logout_model)
    @auth_ns.response(400, 'Invalid or missing token')
    @auth_ns.response(404, 'Refresh token not found')
    @auth_ns.response(500, 'Server error')
    @jwt_required(optional=True)  # Use optional=True to allow processing even if the token has expired
    def post(self):
        """Logout user by revoking the refresh token and blacklisting the access token."""
        try:
            # Attempt to get the current user's identity, handle if the token has expired
            try:
                current_user = get_jwt_identity()
                jti_access = get_jwt().get('jti')
            except ExpiredSignatureError:
                # Decode the token manually without checking expiration
                token = request.headers.get('Authorization').split()[1]  # Extract the token from the header
                decoded_token = decode_token(token, allow_expired=True)
                current_user = decoded_token['sub']
                jti_access = decoded_token.get('jti')
                logger.info(f"Expired token used for logout for user {current_user['email']}")

            # Retrieve and revoke the refresh token for this user
            refresh_token = RefreshToken.query.filter_by(user_id=current_user['id'], revoked=False).first()
            if refresh_token:
                refresh_token.revoke()
                logger.info(f"Refresh token for user {current_user['email']} revoked.")
            else:
                logger.warning(f"No active refresh token found for user {current_user['email']}.")
                return {'message': 'No active refresh token to revoke'}, 404

            # Blacklist the current access token (if valid and not already blacklisted)
            if jti_access:
                token_blacklist = TokenBlacklist.query.filter_by(jti=jti_access).first()
                if not token_blacklist:
                    token_blacklist = TokenBlacklist(
                        jti=jti_access,
                        user_id=current_user['id'],
                        token_type='access',
                        revoked=True,
                        expire_at=datetime.utcnow() + timedelta(days=1)  # Set an appropriate expiry time
                    )
                    db.session.add(token_blacklist)
                    logger.info(f"Access token {jti_access} for user {current_user['email']} blacklisted.")

            # End the user's active session(s)
            active_sessions = UserSession.query.filter_by(user_id=current_user['id'], is_active=True).all()
            for session in active_sessions:
                session.logout_time = datetime.utcnow()
                session.is_active = False
            db.session.commit()  # Commit the session updates to the database
            logger.info(f"All active sessions for user {current_user['email']} ended.")

            # Log the logout in the audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='LOGOUT',
                resource_type='user',
                resource_id=current_user['id'],
                details=f"User {current_user['email']} logged out and refresh token revoked."
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"User {current_user['email']} logged out successfully.")
            return {'message': 'Logged out successfully'}, 200

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            db.session.rollback()
            return {'message': 'An error occurred during logout. Please try again.'}, 500

# Revoke refresh token on logout or explicitly revoke it via this resource
@auth_ns.route('/revoke_refresh')
class RevokeRefreshTokenResource(Resource):
    @auth_ns.doc(description='Revoke a refresh token explicitly.')
    @auth_ns.response(200, 'Success', model=logout_model)
    @auth_ns.response(404, 'Refresh token not found')
    @auth_ns.response(500, 'Server error')
    @jwt_required(refresh=True)  # Ensure this endpoint only accepts refresh tokens
    def post(self):
        """Revoke the refresh token explicitly."""
        try:
            current_user = get_jwt_identity()

            jti = get_jwt()['jti']
            refresh_token = RefreshToken.query.filter_by(token=jti, user_id=current_user['id'], revoked=False).first()

            if not refresh_token:
                logger.warning(f"Refresh token not found or already revoked for user {current_user['email']}")
                return {'message': 'Refresh token not found or already revoked'}, 404

            refresh_token.revoke()

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

        except Exception as e:
            logger.error(f"Error during refresh token revocation: {str(e)}")
            db.session.rollback()
            return {'message': 'An error occurred during refresh token revocation. Please try again.'}, 500
