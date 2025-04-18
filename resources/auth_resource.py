from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt, decode_token
)
from jwt.exceptions import ExpiredSignatureError
from models.user_model import User, UserStatus
from models.user_session_model import UserSession
from models.audit_model import AuditTrail, AuditAction
from models.token_model import TokenBlacklist, RefreshToken
from extensions import db
from utils import get_client_ip
from datetime import datetime, timedelta
import secrets
import json
import re
import ipaddress
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Define a namespace for auth-related operations
auth_ns = Namespace('auth', description='Authentication operations')

# Define models for Swagger documentation
login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

logout_model = auth_ns.model('Logout', {
    'refresh_token': fields.String(required=True, description='Refresh token')
})

session_model = auth_ns.model('Session', {
    'session_id': fields.String(description='Session ID'),
    'created_at': fields.DateTime(description='Session creation time'),
    'last_activity': fields.DateTime(description='Last activity time'),
    'ip_address': fields.String(description='IP address'),
    'user_agent': fields.String(description='User agent')
})

# Utility function to check admin privileges
def is_admin() -> bool:
    current_user = get_jwt_identity()
    return current_user.get('role') == 'admin'

def validate_password_strength(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def get_device_fingerprint() -> str:
    """Generate a device fingerprint based on request headers."""
    headers = request.headers
    fingerprint = {
        'user_agent': headers.get('User-Agent'),
        'accept_language': headers.get('Accept-Language'),
        'accept_encoding': headers.get('Accept-Encoding'),
        'platform': headers.get('Sec-Ch-Ua-Platform'),
        'mobile': headers.get('Sec-Ch-Ua-Mobile'),
    }
    return secrets.token_hex(16) + json.dumps(fingerprint)

def admin_required(f):
    """Decorator to check if the current user is an admin."""
    def wrapper(*args, **kwargs):
        if not is_admin():
            return {'message': 'Admin privileges required'}, 403
        return f(*args, **kwargs)
    return wrapper

def validate_session_location(session: UserSession) -> bool:
    """Validate if the current request location matches the session location."""
    current_ip = get_client_ip()
    try:
        # Compare IP addresses
        if current_ip != session.ip_address:
            # Check if IPs are in the same network (e.g., same ISP)
            current_network = ipaddress.ip_network(current_ip + '/24', strict=False)
            session_network = ipaddress.ip_network(session.ip_address + '/24', strict=False)
            return current_network.overlaps(session_network)
        return True
    except Exception as e:
        logger.error(f"Error validating session location: {str(e)}")
        return False

def check_session_security(session: UserSession) -> bool:
    """Check various security aspects of a session."""
    # Check session expiration
    if session.expires_at <= datetime.utcnow():
        return False

    # Check token expiration
    if session.token_expires_at <= datetime.utcnow():
        return False

    # Check suspicious activity
    if session.suspicious_activity:
        return False

    # Check location
    if not validate_session_location(session):
        return False

    # Check inactivity timeout
    if session.last_activity:
        inactivity_timeout = timedelta(minutes=30)  # Configurable
        if datetime.utcnow() - session.last_activity > inactivity_timeout:
            return False

    return True

# Authentication resource class for login
@auth_ns.route('/login')
class LoginResource(Resource):
    @auth_ns.expect(auth_ns.model('LoginCredentials', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password')
    }), validate=True)
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(401, 'Invalid credentials')
    @auth_ns.response(403, 'Account locked')
    def post(self):
        """Login user and return JWT access and refresh tokens."""
        try:
            data = request.json
            email = data.get('email')
            password = data.get('password')

            user = User.query.filter_by(email=email).first()

            if not user:
                logger.warning(f"Failed login attempt for non-existent email {email}")
                return {'message': 'Invalid credentials'}, 401

            if user.status == UserStatus.LOCKED.value:
                logger.warning(f"Login attempt for locked account {email}")
                return {'message': 'Account is locked. Please contact support.'}, 403

            if user.status == UserStatus.SUSPENDED.value:
                logger.warning(f"Login attempt for suspended account {email}")
                return {'message': 'Account is suspended. Please contact support.'}, 403

            if not user.check_password(password):
                logger.warning(f"Failed login attempt for user {email}")
                return {'message': 'Invalid credentials'}, 401

            # End any active sessions for this user
            active_sessions = UserSession.get_active_sessions(user.id)
            for session in active_sessions:
                session.end_session()
                logger.info(f"Ended previous session for user {email} to maintain single session")

            # Check for suspicious activity
            device_fingerprint = get_device_fingerprint()
            if device_fingerprint not in json.loads(user.device_history or '[]'):
                logger.warning(f"New device detected for user {email}")

            # Revoke old refresh tokens
            old_refresh_token = RefreshToken.query.filter_by(
                user_id=user.id,
                revoked=False
            ).first()
            if old_refresh_token:
                old_refresh_token.revoke()
                logger.info(f"Old refresh token for user {user.email} revoked")

            # Set access and refresh token expiration times
            access_token_expiry = timedelta(hours=1)
            refresh_token_expiry = timedelta(hours=12)

            access_token = create_access_token(
                identity={
                    'id': user.id,
                    'email': user.email,
                    'role': user.role.name
                },
                expires_delta=access_token_expiry
            )
            refresh_token = create_refresh_token(
                identity={
                    'id': user.id,
                    'email': user.email,
                    'role': user.role.name
                },
                expires_delta=refresh_token_expiry
            )

            # Create new session
            session_expiry = datetime.utcnow() + access_token_expiry
            session = UserSession(
                user_id=user.id,
                ip_address=get_client_ip(),
                expires_at=session_expiry,
                user_agent=request.headers.get('User-Agent'),
                device_fingerprint=device_fingerprint
            )
            db.session.add(session)

            # Create refresh token record
            refresh_token_record = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                expire_at=datetime.utcnow() + refresh_token_expiry
            )
            db.session.add(refresh_token_record)

            # Update user activity
            user.update_login_history(device_fingerprint)
            user.update_device_history(device_fingerprint)
            user.update_activity()

            # Log the login
            AuditTrail.log_action(
                user_id=user.id,
                action=AuditAction.LOGIN,
                resource_type='user',
                resource_id=user.id,
                details=f"User {user.email} logged in successfully",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            db.session.commit()

            logger.info(f"User {user.email} logged in successfully")
            return {
                'message': 'Logged in successfully',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expiry': access_token_expiry.total_seconds(),
                'user': user.serialize()
            }, 200

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            db.session.rollback()
            return {'message': 'An error occurred during login'}, 500

# Refresh token endpoint
@auth_ns.route('/refresh')
class RefreshTokenResource(Resource):
    @auth_ns.doc(description='Use the refresh token to get a new access token.')
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(401, 'Invalid or expired refresh token')
    @jwt_required(refresh=True)
    def post(self):
        """Generate a new access token using a valid refresh token."""
        try:
            current_user = get_jwt_identity()
            user = User.query.get(current_user['id'])

            if not user or user.status != UserStatus.ACTIVE.value:
                logger.warning(f"Token refresh attempt for inactive user {current_user['email']}")
                return {'message': 'User account is not active'}, 401

            # Check if the refresh token has expired
            jti_refresh = get_jwt()['jti']
            refresh_token_record = RefreshToken.query.filter_by(
                token=jti_refresh,
                user_id=current_user['id'],
                revoked=False
            ).first()

            if not refresh_token_record or refresh_token_record.expire_at < datetime.utcnow():
                logger.error(f"Refresh token for user {current_user['email']} has expired or been revoked")
                return {'message': 'Refresh token has expired or been revoked'}, 401

            # Create a new access token
            access_token = create_access_token(
                identity=current_user,
                expires_delta=timedelta(hours=1)
            )

            # Update session activity
            session = UserSession.query.filter_by(
                user_id=current_user['id'],
                is_active=True
            ).first()
            if session:
                session.update_last_activity()

            # Log the refresh
            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.REFRESH,
                resource_type='user',
                resource_id=current_user['id'],
                details=f"User {current_user['email']} token refreshed successfully",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            logger.info(f"User {current_user['email']} refreshed their access token")
            return {
                'message': 'Access token refreshed successfully',
                'access_token': access_token,
                'expiry': timedelta(hours=1).total_seconds(),
                'user': user.serialize()
            }, 200

        except ExpiredSignatureError:
            logger.error("Attempted refresh with an expired token")
            return {'message': 'The refresh token has expired. Please log in again.'}, 401
        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}")
            db.session.rollback()
            return {'message': 'An error occurred during token refresh'}, 500

# Logout resource class
@auth_ns.route('/logout')
class LogoutResource(Resource):
    @auth_ns.doc(description='Logs the user out by revoking the refresh token and blacklisting the access token.')
    @auth_ns.response(200, 'Success', model=logout_model)
    @auth_ns.response(400, 'Invalid or missing token')
    @auth_ns.response(404, 'Refresh token not found')
    @auth_ns.response(500, 'Server error')
    @jwt_required(optional=True)
    def post(self):
        """Logout user by revoking the refresh token and blacklisting the access token."""
        try:
            # Attempt to get the current user's identity
            try:
                current_user = get_jwt_identity()
                jwt_data = get_jwt()
                jti_access = jwt_data.get('jti')
                exp = datetime.fromtimestamp(jwt_data.get('exp', 0))
            except ExpiredSignatureError:
                token = request.headers.get('Authorization').split()[1]
                decoded_token = decode_token(token, allow_expired=True)
                current_user = decoded_token['sub']
                jti_access = decoded_token.get('jti')
                exp = datetime.fromtimestamp(decoded_token.get('exp', 0))
                logger.info(f"Expired token used for logout for user {current_user['email']}")

            # Use no_autoflush to prevent premature flushes
            with db.session.no_autoflush:
                # Retrieve and revoke the refresh token
                refresh_token = RefreshToken.query.filter_by(
                    user_id=current_user['id'],
                    revoked=False
                ).first()
                if refresh_token:
                    refresh_token.revoke()
                    logger.info(f"Refresh token for user {current_user['email']} revoked")
                else:
                    logger.warning(f"No active refresh token found for user {current_user['email']}")
                    return {'message': 'No active refresh token to revoke'}, 404

                # Blacklist the access token
                if jti_access:
                    blacklisted_token = TokenBlacklist(
                        jti=jti_access,
                        token_type='access',
                        user_id=current_user['id'],
                        expire_at=exp  # Set the expiration time from the token
                    )
                    db.session.add(blacklisted_token)

                # End active sessions
                active_sessions = UserSession.get_active_sessions(current_user['id'])
                for session in active_sessions:
                    session.end_session()

                # Log the logout
                AuditTrail.log_action(
                    user_id=current_user['id'],
                    action=AuditAction.LOGOUT,
                    resource_type='user',
                    resource_id=current_user['id'],
                    details=f"User {current_user['email']} logged out successfully",
                    ip_address=get_client_ip(),
                    user_agent=request.headers.get('User-Agent')
                )

            # Commit all changes at once
            db.session.commit()
            logger.info(f"User {current_user['email']} logged out successfully")
            return {'message': 'Logged out successfully'}, 200

        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            db.session.rollback()
            return {'message': 'An error occurred during logout'}, 500

@auth_ns.route('/session/rotate')
class SessionRotationResource(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Rotate the current session token."""
        try:
            current_user = get_jwt_identity()
            session = UserSession.query.filter_by(
                user_id=current_user['id'],
                is_active=True
            ).first()

            if not session:
                return {'message': 'No active session found'}, 404

            new_token = session.rotate_token()

            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.UPDATE,
                resource_type='session',
                resource_id=session.id,
                details='Session token rotated',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            return {
                'message': 'Session token rotated',
                'new_token': new_token
            }, 200

        except Exception as e:
            logger.error(
                f"Error rotating session token: {str(e)}"
            )
            return {'message': 'Error rotating session token'}, 500

@auth_ns.route('/session/cleanup')
class SessionCleanupResource(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    def post(self):
        """Clean up expired sessions."""
        try:
            cleaned_count = UserSession.cleanup_expired_sessions()

            AuditTrail.log_action(
                user_id=get_jwt_identity()['id'],
                action=AuditAction.CLEANUP,
                resource_type='session',
                details=f'Cleaned up {cleaned_count} expired sessions',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            return {'message': f'Cleaned up {cleaned_count} expired sessions'}, 200
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return {'message': 'Error cleaning up sessions'}, 500

@auth_ns.route('/session/activity')
class SessionActivityResource(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @jwt_required()
    @auth_ns.marshal_list_with(session_model)
    def get(self):
        """Get current user's active sessions."""
        try:
            current_user = get_jwt_identity()
            sessions = UserSession.get_active_sessions(current_user['id'])
            return sessions, 200
        except Exception as e:
            logger.error(f"Error getting session activity: {str(e)}")
            return {'message': 'Error getting session activity'}, 500

@auth_ns.route('/session/<int:session_id>')
class SessionManagementResource(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, session_id):
        """End a specific session."""
        try:
            current_user = get_jwt_identity()
            session = UserSession.query.filter_by(
                id=session_id,
                user_id=current_user['id']
            ).first()

            if not session:
                return {'message': 'Session not found'}, 404

            session.end_session()

            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.LOGOUT,
                resource_type='session',
                resource_id=session_id,
                details='Session ended manually',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            return {'message': 'Session ended successfully'}, 200
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return {'message': 'Error ending session'}, 500

@auth_ns.route('/status')
class UserStatusResource(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Check current user's status and session information."""
        try:
            current_user = get_jwt_identity()
            user = User.query.get(current_user['id'])

            if not user:
                return {'message': 'User not found'}, 404

            active_sessions = UserSession.get_active_sessions(user.id)
            session_info = [session.serialize() for session in active_sessions]

            return {
                'user_status': user.status,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'failed_attempts': user.failed_attempts,
                'is_locked': user.status == UserStatus.LOCKED.value,
                'active_sessions': session_info
            }, 200
        except Exception as e:
            logger.error(f"Error getting user status: {str(e)}")
            return {'message': 'Error getting user status'}, 500

@auth_ns.route('/session/end-all')
class EndAllSessionsResource(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    def post(self):
        """End all active sessions for all users."""
        try:
            # Get current admin user for audit
            admin_user = get_jwt_identity()

            # Get all active sessions
            active_sessions = UserSession.query.filter_by(is_active=True).all()
            session_count = len(active_sessions)

            # End each session
            for session in active_sessions:
                session.end_session()

            # Log the action
            AuditTrail.log_action(
                user_id=admin_user['id'],
                action=AuditAction.UPDATE,
                resource_type='session',
                details=f'Ended {session_count} active sessions across all users',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            db.session.commit()
            return {
                'message': f'Successfully ended {session_count} active sessions'
            }, 200

        except Exception as e:
            logger.error(f"Error ending all sessions: {str(e)}")
            db.session.rollback()
            return {'message': 'Error ending all sessions'}, 500
