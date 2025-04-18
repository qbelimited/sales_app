from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import User, Role
from models.branch_model import Branch
from models.user_session_model import UserSession
from models.audit_model import AuditTrail
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from datetime import datetime, timedelta
from utils import get_client_ip
import json
import re
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Define a namespace for User-related operations
user_ns = Namespace('user', description='User operations')

# Define models for Swagger documentation
user_model = user_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(required=True, description='User Email'),
    'name': fields.String(required=True, description='User Name'),
    'role_id': fields.Integer(required=True, description='Role ID'),
    'branches': fields.List(fields.Integer, description='List of Branch IDs'),
    'is_active': fields.Boolean(description='Is Active'),
    'is_deleted': fields.Boolean(description='Is Deleted'),
    'status': fields.String(
        description='User Status (active, inactive, suspended, locked)'
    ),
    'failed_login_attempts': fields.Integer(description='Failed Login Attempts'),
    'last_login': fields.DateTime(description='Last Login Time'),
    'last_activity': fields.DateTime(description='Last Activity Time'),
    'current_device': fields.String(description='Current Device Info'),
    'created_at': fields.String(description='Created At'),
    'updated_at': fields.String(description='Updated At'),
})

password_model = user_ns.model('Password', {
    'current_password': fields.String(required=True, description='Current Password'),
    'new_password': fields.String(required=True, description='New Password'),
})

session_model = user_ns.model('UserSession', {
    'id': fields.Integer(description='Session ID'),
    'user_id': fields.Integer(description='User ID'),
    'login_time': fields.DateTime(description='Login Time'),
    'logout_time': fields.DateTime(description='Logout Time'),
    'expires_at': fields.DateTime(description='Expires At'),
    'ip_address': fields.String(description='IP Address'),
    'is_active': fields.Boolean(description='Is Active'),
})

# Token settings
TOKEN_GRACE_PERIOD = 5  # minutes
TOKEN_EXPIRATION_WARNING = 10  # minutes
TOKEN_REFRESH_THRESHOLD = 15  # minutes before expiration to refresh
MAX_REFRESH_ATTEMPTS = 3  # Maximum number of refresh attempts per session
USER_ACTIVITY_TIMEOUT = 30  # minutes of inactivity before considering user inactive

@lru_cache(maxsize=100)
def validate_email_format(email):
    """Validate email format with caching."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@lru_cache(maxsize=100)
def validate_password_strength(password):
    """Validate password strength with caching."""
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number'
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password must contain at least one special character'
    return True, 'Password is valid'


def validate_user_data(data, user_id=None):
    """Validate all user data before creation or update."""
    # Validate required fields
    required_fields = ['email', 'name', 'role_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f'Missing required fields: {", ".join(missing_fields)}')

    # Validate email format and uniqueness
    if 'email' in data:
        if not validate_email_format(data['email']):
            raise ValueError('Invalid email format')

        # Check email uniqueness
        query = User.query.filter_by(email=data['email'], is_deleted=False)
        if user_id:
            query = query.filter(User.id != user_id)
        if query.first():
            raise ValueError('Email already exists')

    # Validate role exists
    if 'role_id' in data:
        role = Role.query.filter_by(id=data['role_id'], is_deleted=False).first()
        if not role:
            raise ValueError('Invalid role ID')

    # Validate branches exist
    if 'branches' in data:
        for branch_id in data['branches']:
            branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
            if not branch:
                raise ValueError(f'Invalid branch ID: {branch_id}')

    # Validate status
    if 'status' in data:
        valid_statuses = ['active', 'inactive', 'suspended', 'locked']
        if data['status'] not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')


def validate_status_transition(current_status, new_status):
    """Validate user status transition."""
    valid_transitions = {
        'active': ['inactive', 'suspended', 'locked'],
        'inactive': ['active', 'suspended', 'locked'],
        'suspended': ['active', 'inactive', 'locked'],
        'locked': ['active', 'inactive', 'suspended']
    }

    if current_status not in valid_transitions:
        raise ValueError(f'Invalid current status: {current_status}')

    if new_status not in valid_transitions[current_status]:
        raise ValueError(f'Invalid status transition from {current_status} to {new_status}')


# CRUD Operations for Users
@user_ns.route('/')
class UserListResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @user_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @user_ns.param('filter_by', 'Filter by User name', type='string')
    @user_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of Users."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        user_query = User.query.filter_by(is_deleted=False)

        if filter_by:
            user_query = user_query.filter(User.name.ilike(f'%{filter_by}%'))

        users = user_query.order_by(sort_by).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to the audit trail and logger
        logger.info(f"User {current_user['id']} accessed the list of users.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='user_list',
            resource_id=None,
            details=f"User {current_user['id']} accessed list of users",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'users': [user.serialize() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': users.page
        }, 200

    @user_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Bad Request', 403: 'Unauthorized'})
    @jwt_required()
    @user_ns.expect(user_model, validate=True)
    def post(self):
        """Create a new User (admin only)."""
        current_user = get_jwt_identity()

        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to create a new user.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate role rules before creating user
        role = Role.query.get(data['role_id'])
        if not role:
            return {'message': 'Role not found'}, 404

        is_valid, error_message = role.validate_rules(data)
        if not is_valid:
            return {'message': error_message}, 400

        new_user = User(
            email=data['email'],
            name=data['name'],
            role_id=data['role_id'],
            status=data.get('status', 'active')
        )

        # Set default password if not provided
        if 'password' not in data:
            new_user.password = "Password"  # Set default password
        else:
            new_user.password = data['password']

        # Assign branches to the user
        if 'branches' in data:
            branches = Branch.query.filter(Branch.id.in_(data['branches'])).all()
            new_user.branches = branches

        try:
            db.session.add(new_user)
            db.session.commit()

            # Increment role usage count
            role.increment_usage()

            # Log the creation to audit trail and logger
            logger.info(f"User {current_user['id']} created a new user with ID {new_user.id}.")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='user',
                resource_id=new_user.id,
                details=f"User created a new User with ID {new_user.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return new_user.serialize(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return {'message': 'Error creating user'}, 500


@user_ns.route('/<int:user_id>')
class UserResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found'})
    @jwt_required()
    def get(self, user_id):
        """Retrieve a specific User by ID."""
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            logger.error(f"User with ID {user_id} not found for User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        # Log the access to audit trail and logger
        logger.info(f"User {current_user['id']} accessed details of User {user_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='user',
            resource_id=user_id,
            details=f"User accessed details of User with ID {user_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return user.serialize(), 200

    @user_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'User not found', 403: 'Unauthorized'})
    @jwt_required()
    @user_ns.expect(user_model, validate=True)
    def put(self, user_id):
        """Update an existing User (self or admin only)."""
        current_user = get_jwt_identity()

        # Only allow the user themselves or an admin to update
        if current_user['id'] != user_id and current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(f"Unauthorized update attempt by User {current_user['id']} on User {user_id}.")
            return {'message': 'Unauthorized'}, 403

        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            logger.error(f"User with ID {user_id} not found for update by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        data = request.json

        # If role is being changed, validate the new role rules
        if 'role_id' in data and data['role_id'] != user.role_id:
            new_role = Role.query.get(data['role_id'])
            if not new_role:
                return {'message': 'New role not found'}, 404

            # Validate the new role rules and update role usage counts
            # if validation passes
            is_valid, error_message = new_role.validate_rules(data)
            if not is_valid:
                return {'message': error_message}, 400

            # Update role usage counts
            user.role.decrement_usage()
            new_role.increment_usage()

        # Update user fields
        user.email = data.get('email', user.email)
        user.name = data.get('name', user.name)
        user.role_id = data.get('role_id', user.role_id)
        user.status = data.get('status', user.status)
        user.updated_at = datetime.utcnow()

        # Assign branches to the user
        if 'branches' in data:
            branches = Branch.query.filter(Branch.id.in_(data['branches'])).all()
            user.branches = branches

        try:
            db.session.commit()

            # Log the update to audit trail and logger
            logger.info(f"User {current_user['id']} updated User {user_id}.")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='user',
                resource_id=user.id,
                details=f"User updated User with ID {user.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return user.serialize(), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {str(e)}")
            return {'message': 'Error updating user'}, 500

    @user_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'User not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, user_id):
        """Soft-delete a User (admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized deletion attempt by User {current_user['id']} on User {user_id}.")
            return {'message': 'Unauthorized'}, 403

        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            logger.error(f"User with ID {user_id} not found for deletion by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        user.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail and logger
        logger.info(f"User {current_user['id']} deleted User {user_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='user',
            resource_id=user.id,
            details=f"User deleted User with ID {user.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'User deleted successfully'}, 200


# Password Update Resource
@user_ns.route('/<int:user_id>/password')
class PasswordUpdateResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @user_ns.expect(password_model, validate=True)
    @jwt_required()
    def put(self, user_id):
        """Update the password for the authenticated user or admin."""
        current_user = get_jwt_identity()

        # Ensure that only the user themselves or an admin can update their password
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return {'message': 'User not found'}, 404

        data = request.json
        current_password = data['current_password']
        new_password = data['new_password']

        # If the current user is not an admin, verify the current password
        if current_user['role'].lower() != 'admin' and not user.check_password(current_password):
            return {'message': 'Current password is incorrect'}, 400

        # Update the password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        db.session.commit()

        # Log the password update to the audit trail and logger
        logger.info(f"User {current_user['id']} updated password for user {user_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='user',
            resource_id=user_id,
            details=f"User updated password",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Password updated successfully'}, 200


def handle_token_expiration():
    """Handle token expiration and logout user."""
    try:
        current_user = get_jwt_identity()
        if current_user:
            # End all active sessions for the user
            active_sessions = UserSession.query.filter_by(
                user_id=current_user['id'],
                is_active=True
            ).all()

            for session in active_sessions:
                session.end_session()
                logger.info(f"Session {session.id} ended due to token expiration")

            db.session.commit()
    except Exception as e:
        logger.error(f"Error handling token expiration: {str(e)}")


def check_token_expiration():
    """Check if token is expired or about to expire."""
    try:
        jwt_data = get_jwt()
        expiration_time = datetime.fromtimestamp(jwt_data['exp'])
        current_time = datetime.utcnow()

        # Check if token is expired (including grace period)
        if expiration_time < current_time - timedelta(minutes=TOKEN_GRACE_PERIOD):
            handle_token_expiration()
            return False, 'Token expired'

        # Check if token is about to expire (for warning)
        if expiration_time < current_time + timedelta(minutes=TOKEN_EXPIRATION_WARNING):
            return True, 'Token about to expire'

        return True, None
    except Exception as e:
        logger.error(f"Error checking token expiration: {str(e)}")
        return False, 'Error checking token'


def is_user_active(user_id):
    """Check if user has been active recently."""
    try:
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return False

        last_activity = user.last_activity
        if not last_activity:
            return False

        inactive_time = datetime.utcnow() - last_activity
        return inactive_time < timedelta(minutes=USER_ACTIVITY_TIMEOUT)
    except Exception as e:
        logger.error(f"Error checking user activity: {str(e)}")
        return False


def refresh_token_if_needed():
    """Refresh token if it's about to expire and user is active."""
    try:
        jwt_data = get_jwt()
        expiration_time = datetime.fromtimestamp(jwt_data['exp'])
        current_time = datetime.utcnow()

        # Check if token needs refresh
        if expiration_time < current_time + timedelta(minutes=TOKEN_REFRESH_THRESHOLD):
            current_user = get_jwt_identity()
            if current_user and is_user_active(current_user['id']):
                # Create new token with same identity
                new_token = create_access_token(
                    identity=current_user,
                    expires_delta=timedelta(minutes=30)  # Standard token lifetime
                )
                logger.info(f"Token refreshed for user {current_user['id']}")
                return new_token
            else:
                logger.warning(
                    f"Token refresh skipped - user inactive or not found: "
                    f"{current_user['id'] if current_user else 'None'}"
                )
        return None
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None


@user_ns.route('/<int:user_id>/sessions')
class UserSessionResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self, user_id):
        """Get user sessions with automatic token refresh."""
        try:
            # Check token expiration with grace period
            is_valid, message = check_token_expiration()
            if not is_valid:
                return {'message': message}, 401

            # Attempt to refresh token if needed
            new_token = refresh_token_if_needed()
            if new_token:
                return {
                    'message': 'Token refreshed',
                    'new_token': new_token
                }, 200

            current_user = get_jwt_identity()
            if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
                return {'message': 'Unauthorized'}, 403

            # Update user's last activity
            user = User.query.filter_by(id=user_id).first()
            if user:
                user.last_activity = datetime.utcnow()
                db.session.commit()

            sessions = UserSession.query.filter_by(user_id=user_id).all()
            return [session.serialize() for session in sessions], 200
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return {'message': 'An error occurred'}, 500

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.expect(session_model, validate=True)
    def post(self, user_id):
        """Create a new session for a user."""
        current_user = get_jwt_identity()

        # Only admin or the user themselves can create a session
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        # End any existing active sessions for this user
        existing_sessions = UserSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()

        for session in existing_sessions:
            session.end_session()
            logger.info(
                f"Ended existing session {session.id} for user {user_id} "
                f"before creating new session"
            )

        data = request.json

        new_session = UserSession(
            user_id=user_id,
            ip_address=data.get('ip_address', '0.0.0.0'),
            login_time=datetime.utcnow(),
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(minutes=45)
        )
        db.session.add(new_session)
        db.session.commit()

        logger.info(
            f"User {current_user['id']} created a new session for user {user_id}"
        )
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='session',
            resource_id=new_session.id,
            details=f"Created session for user {user_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return new_session.serialize(), 201

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.response(200, 'Sessions ended successfully')
    @user_ns.response(404, 'No active sessions found')
    def delete(self, user_id):
        """End all active sessions for a user (admin only)."""
        current_user = get_jwt_identity()

        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        sessions = UserSession.get_active_sessions(user_id=user_id)
        if not sessions:
            return {'message': 'No active sessions found'}, 404

        for session in sessions:
            session.end_session()
            logger.info(
                f"Admin {current_user['id']} ended session {session.id} "
                f"for user {user_id}"
            )

        # Add audit trail entry
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='user_sessions',
            resource_id=user_id,
            details=f"Ended all active sessions for user {user_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'All active sessions ended successfully'}, 200


@user_ns.route('/<int:user_id>/sessions/<int:session_id>')
class SingleUserSessionResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.response(200, 'Session retrieved successfully', session_model)
    @user_ns.response(404, 'Session not found')
    def get(self, user_id, session_id):
        """Retrieve a specific session for a user."""
        current_user = get_jwt_identity()

        # Only admin or the user themselves can access session details
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        session = UserSession.query.filter_by(id=session_id, user_id=user_id, is_active=True).first()
        if not session:
            return {'message': 'Session not found'}, 404

        # Log the access to the logger
        logger.info(f"User {current_user['id']} accessed session {session_id} for user {user_id}.")

        # Add audit trail entry
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='user_session',
            resource_id=session_id,
            details=f"Accessed session {session_id} for user {user_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return session.serialize(), 200

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.response(200, 'Session updated successfully')
    @user_ns.response(404, 'Session not found')
    def put(self, user_id, session_id):
        """Update a specific session for a user."""
        current_user = get_jwt_identity()

        # Only admin or the user themselves can update session details
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        session = UserSession.query.filter_by(id=session_id, user_id=user_id, is_active=True).first()
        if not session:
            return {'message': 'Session not found'}, 404

        session.logout_time = datetime.utcnow()
        session.is_active = False

        db.session.commit()

        logger.info(f"User {current_user['id']} updated session {session_id} for user {user_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='session',
            resource_id=session_id,
            details=f"Updated session {session_id} for user {user_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Session updated successfully'}, 200

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.response(200, 'Session deleted successfully')
    @user_ns.response(404, 'Session not found')
    def delete(self, user_id, session_id):
        """End a specific session for a user (admin only)."""
        current_user = get_jwt_identity()

        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        session = UserSession.query.filter_by(id=session_id, user_id=user_id, is_active=True).first()
        if not session:
            return {'message': 'Session not found'}, 404

        session.end_session()
        logger.info(f"User {current_user['id']} ended session {session_id} for user {user_id}.")

        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='session',
            resource_id=session_id,
            details=f"Ended session {session_id} for user {user_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Session deleted successfully'}, 200


# All User Sessions Management
@user_ns.route('/sessions')
class AllUserSessionsResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @user_ns.param('per_page', 'Number of items per page', type='integer', default=1000)
    @user_ns.param('filter_by', 'Filter by User ID or User name', type='string')
    @user_ns.param('sort_by', 'Sort by field (e.g., login_time, user_id)', type='string', default='login_time')
    def get(self):
        """Retrieve all sessions for all users (authenticated users)."""
        current_user = get_jwt_identity()

        # Handle pagination and sorting
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'login_time')

        session_query = UserSession.query

        # Optional filtering by user ID or name
        if filter_by:
            user_ids = [user.id for user in User.query.filter(User.name.ilike(f'%{filter_by}%')).all()]
            session_query = session_query.filter(UserSession.user_id.in_(user_ids))

        # Sorting and pagination
        sessions = session_query.order_by(sort_by).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to the audit trail and logger
        logger.info(f"User {current_user['id']} accessed the list of all user sessions.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='session_list',
            resource_id=None,
            details=f"User accessed list of all user sessions"
        )
        db.session.add(audit)
        db.session.commit()

        # Include user names in the serialized session data
        session_data = []
        for session in sessions.items:
            user = User.query.get(session.user_id)
            session_info = session.serialize()
            session_info['user_name'] = user.name if user else 'Unknown'
            session_data.append(session_info)

        return {
            'sessions': session_data,
            'total': sessions.total,
            'pages': sessions.pages,
            'current_page': sessions.page
        }, 200


@user_ns.route('/<int:user_id>/status')
class UserStatusResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found', 403: 'Unauthorized'})
    @jwt_required()
    @user_ns.param('status', 'New status (active, inactive, suspended, locked)', required=True)
    def put(self, user_id):
        """Update user status (admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized status update attempt by User {current_user['id']} on User {user_id}.")
            return {'message': 'Unauthorized'}, 403

        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            logger.error(f"User with ID {user_id} not found for status update by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        new_status = request.args.get('status')
        try:
            user.status = new_status
            db.session.commit()

            # Log the status update to audit trail and logger
            logger.info(f"User {current_user['id']} updated status of User {user_id} to {new_status}.")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE_STATUS',
                resource_type='user',
                resource_id=user.id,
                details=f"User updated status of User {user.id} to {new_status}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': f'User status updated to {new_status}'}, 200
        except ValueError as e:
            return {'message': str(e)}, 400


@user_ns.route('/<int:user_id>/activity')
class UserActivityResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found'})
    @jwt_required()
    def get(self, user_id):
        """Get user activity information."""
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            logger.error(f"User with ID {user_id} not found for activity check by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        # Only allow users to view their own activity or admins to view any user's activity
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized activity access attempt by User {current_user['id']} on User {user_id}.")
            return {'message': 'Unauthorized'}, 403

        activity_data = {
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'last_activity': user.last_activity.isoformat() if user.last_activity else None,
            'current_device': user.current_device,
            'login_history': json.loads(user.login_history) if user.login_history else [],
            'device_history': json.loads(user.device_history) if user.device_history else [],
            'failed_login_attempts': user.failed_login_attempts,
            'account_locked_until': user.account_locked_until.isoformat() if user.account_locked_until else None
        }

        return activity_data, 200


@user_ns.route('/roles/hierarchy')
class RoleHierarchyResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success'})
    @jwt_required()
    @user_ns.param('role_id', 'Optional role ID to get specific role hierarchy', type='integer')
    def get(self):
        """Get role hierarchy."""
        role_id = request.args.get('role_id', type=int)
        hierarchy = Role.get_role_hierarchy(role_id)
        return {'hierarchy': hierarchy}, 200


@user_ns.route('/roles/validate')
class RoleValidationResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 400: 'Validation Failed'})
    @jwt_required()
    @user_ns.expect(user_model, validate=True)
    def post(self):
        """Validate user data against role rules."""
        data = request.json
        role_id = data.get('role_id')
        if not role_id:
            return {'message': 'Role ID is required'}, 400

        role = Role.query.get(role_id)
        if not role:
            return {'message': 'Role not found'}, 404

        is_valid, error_message = role.validate_rules(data)
        if not is_valid:
            return {'message': error_message}, 400

        return {'message': 'Validation successful'}, 200


@user_ns.route('/<int:user_id>/permissions')
class UserPermissionsResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found'})
    @jwt_required()
    def get(self, user_id):
        """Get user's effective permissions."""
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()

        if not user:
            logger.error(f"User with ID {user_id} not found for permissions check by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        # Only allow users to view their own permissions or admins to view any user's permissions
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized permissions access attempt by User {current_user['id']} on User {user_id}.")
            return {'message': 'Unauthorized'}, 403

        permissions = user.get_effective_permissions()
        return {'permissions': permissions}, 200


@user_ns.route('/<int:user_id>/check-permission')
class CheckPermissionResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found'})
    @jwt_required()
    @user_ns.param('permission', 'Permission to check', required=True)
    def get(self, user_id):
        """Check if user has a specific permission."""
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()

        if not user:
            logger.error(f"User with ID {user_id} not found for permission check by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        permission = request.args.get('permission')
        if not permission:
            return {'message': 'Permission parameter is required'}, 400

        has_permission = user.check_permission(permission)
        return {'has_permission': has_permission}, 200


@user_ns.route('/sessions/expired')
class ExpiredSessionsResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success'})
    @jwt_required()
    @user_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @user_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    def get(self):
        """Get all expired sessions."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        expired_sessions = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'sessions': [session.serialize() for session in expired_sessions.items],
            'total': expired_sessions.total,
            'pages': expired_sessions.pages,
            'current_page': expired_sessions.page
        }, 200


@user_ns.route('/sessions/analytics')
class SessionAnalyticsResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success'})
    @jwt_required()
    @user_ns.param('start_date', 'Start date for analytics (YYYY-MM-DD)', required=True)
    @user_ns.param('end_date', 'End date for analytics (YYYY-MM-DD)', required=True)
    def get(self):
        """Get session analytics for a date range."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
        except ValueError:
            return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        # Get total sessions
        total_sessions = UserSession.query.filter(
            UserSession.login_time.between(start_date, end_date)
        ).count()

        # Get active sessions
        active_sessions = UserSession.query.filter(
            UserSession.login_time.between(start_date, end_date),
            UserSession.is_active == True
        ).count()

        # Get average session duration
        sessions = UserSession.query.filter(
            UserSession.login_time.between(start_date, end_date),
            UserSession.logout_time.isnot(None)
        ).all()

        total_duration = sum(
            (session.logout_time - session.login_time).total_seconds()
            for session in sessions
        )
        avg_duration = total_duration / len(sessions) if sessions else 0

        # Get sessions by role
        role_stats = {}
        for role in Role.query.all():
            role_sessions = UserSession.query.join(User).filter(
                User.role_id == role.id,
                UserSession.login_time.between(start_date, end_date)
            ).count()
            role_stats[role.name] = role_sessions

        analytics = {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'average_session_duration_seconds': avg_duration,
            'sessions_by_role': role_stats,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }

        return analytics, 200


@user_ns.route('/<int:user_id>/sessions/activity')
class SessionActivityResource(Resource):
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found'})
    @jwt_required()
    def get(self, user_id):
        """Get detailed session activity for a user."""
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()

        if not user:
            return {'message': 'User not found'}, 404

        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        # Get all sessions for the user
        sessions = UserSession.query.filter_by(user_id=user_id).all()

        # Calculate session statistics
        total_sessions = len(sessions)
        active_sessions = sum(1 for s in sessions if s.is_active)
        total_duration = sum(
            (s.logout_time - s.login_time).total_seconds()
            for s in sessions
            if s.logout_time is not None
        )
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0

        # Get unique devices
        devices = set(session.ip_address for session in sessions)

        activity_data = {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'average_session_duration_seconds': avg_duration,
            'unique_devices': len(devices),
            'sessions': [session.serialize() for session in sessions]
        }

        return activity_data, 200


def check_role_permission(user, allowed_roles):
    """Check if user has required role permissions."""
    return user['role'].lower() in allowed_roles


@user_ns.route('/<int:user_id>/timeline')
class UserTimelineResource(Resource):
    """Resource for getting user activity timeline."""

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.param('start_date', 'Start date for timeline (YYYY-MM-DD)')
    @user_ns.param('end_date', 'End date for timeline (YYYY-MM-DD)')
    @user_ns.param('event_type', 'Filter by event type (login, logout, status_change, etc.)')
    def get(self, user_id):
        """Get user activity timeline."""
        try:
            current_user = get_jwt_identity()
            if not check_role_permission(current_user, ['admin', 'manager']):
                return {'message': 'Unauthorized'}, 403

            # Get user
            user = User.query.filter_by(id=user_id, is_deleted=False).first()
            if not user:
                return {'message': 'User not found'}, 404

            # Get query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            event_type = request.args.get('event_type')

            # Build timeline query
            timeline_events = []

            # Add login/logout events from sessions
            sessions = UserSession.query.filter_by(user_id=user_id)
            if start_date:
                sessions = sessions.filter(UserSession.login_time >= start_date)
            if end_date:
                sessions = sessions.filter(UserSession.login_time <= end_date)
            if event_type and event_type in ['login', 'logout']:
                sessions = sessions.filter(UserSession.is_active == (event_type == 'login'))

            for session in sessions:
                timeline_events.append({
                    'timestamp': session.login_time,
                    'event_type': 'login',
                    'details': {
                        'ip_address': session.ip_address,
                        'device': session.device_info
                    }
                })
                if session.logout_time:
                    timeline_events.append({
                        'timestamp': session.logout_time,
                        'event_type': 'logout',
                        'details': {
                            'ip_address': session.ip_address,
                            'device': session.device_info
                        }
                    })

            # Add status changes from audit trail
            status_changes = AuditTrail.query.filter(
                AuditTrail.user_id == user_id,
                AuditTrail.resource_type == 'user_status'
            )
            if start_date:
                status_changes = status_changes.filter(AuditTrail.created_at >= start_date)
            if end_date:
                status_changes = status_changes.filter(AuditTrail.created_at <= end_date)
            if event_type and event_type == 'status_change':
                status_changes = status_changes.filter(AuditTrail.action == 'UPDATE')

            for change in status_changes:
                timeline_events.append({
                    'timestamp': change.created_at,
                    'event_type': 'status_change',
                    'details': {
                        'old_status': change.old_value,
                        'new_status': change.new_value,
                        'changed_by': change.changed_by
                    }
                })

            # Sort events by timestamp
            timeline_events.sort(key=lambda x: x['timestamp'])

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='user_timeline',
                resource_id=user_id,
                details=f"User accessed timeline for user {user_id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'user_id': user_id,
                'timeline': timeline_events
            }

        except Exception as e:
            logger.error(f"Error getting user timeline: {str(e)}")
            return {'message': 'An error occurred while fetching timeline'}, 500


@user_ns.route('/bulk')
class BulkUserResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Bulk create users."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            return {'message': 'Unauthorized'}, 403

        try:
            data = request.json
            if not isinstance(data, list):
                return {'message': 'Request body must be a list of users'}, 400

            created_users = []
            errors = []

            for user_data in data:
                try:
                    validate_user_data(user_data)
                    new_user = User(
                        email=user_data['email'],
                        name=user_data['name'],
                        role_id=user_data['role_id'],
                        status=user_data.get('status', 'active')
                    )

                    if 'password' in user_data:
                        new_user.password = user_data['password']
                    else:
                        new_user.password = "Password"  # Set default password

                    if 'branches' in user_data:
                        branches = Branch.query.filter(Branch.id.in_(user_data['branches'])).all()
                        new_user.branches = branches

                    db.session.add(new_user)
                    created_users.append(new_user.serialize())
                except Exception as e:
                    errors.append({
                        'email': user_data.get('email'),
                        'error': str(e)
                    })

            if errors:
                db.session.rollback()
                return {
                    'message': 'Some users could not be created',
                    'errors': errors
                }, 400

            db.session.commit()
            return {'users': created_users}, 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in bulk user creation: {str(e)}")
            return {'message': 'Error creating users'}, 500

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    def put(self):
        """Bulk update users."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            return {'message': 'Unauthorized'}, 403

        try:
            data = request.json
            if not isinstance(data, list):
                return {'message': 'Request body must be a list of user updates'}, 400

            updated_users = []
            errors = []

            for update_data in data:
                try:
                    user_id = update_data.get('id')
                    if not user_id:
                        raise ValueError('User ID is required for updates')

                    user = User.query.get(user_id)
                    if not user:
                        raise ValueError(f'User with ID {user_id} not found')

                    # Update user fields
                    for field in ['name', 'role_id', 'status']:
                        if field in update_data:
                            setattr(user, field, update_data[field])

                    if 'branches' in update_data:
                        branches = Branch.query.filter(Branch.id.in_(update_data['branches'])).all()
                        user.branches = branches

                    updated_users.append(user.serialize())
                except Exception as e:
                    errors.append({
                        'user_id': update_data.get('id'),
                        'error': str(e)
                    })

            if errors:
                db.session.rollback()
                return {
                    'message': 'Some users could not be updated',
                    'errors': errors
                }, 400

            db.session.commit()
            return {'users': updated_users}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in bulk user update: {str(e)}")
            return {'message': 'Error updating users'}, 500

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self):
        """Bulk delete users."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            return {'message': 'Unauthorized'}, 403

        try:
            data = request.json
            if not isinstance(data, list):
                return {'message': 'Request body must be a list of user IDs'}, 400

            deleted_users = []
            errors = []

            for user_id in data:
                try:
                    user = User.query.get(user_id)
                    if not user:
                        raise ValueError(f'User with ID {user_id} not found')

                    user.is_deleted = True
                    user.updated_at = datetime.utcnow()
                    deleted_users.append(user.serialize())
                except Exception as e:
                    errors.append({
                        'user_id': user_id,
                        'error': str(e)
                    })

            if errors:
                db.session.rollback()
                return {
                    'message': 'Some users could not be deleted',
                    'errors': errors
                }, 400

            db.session.commit()
            return {'users': deleted_users}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in bulk user deletion: {str(e)}")
            return {'message': 'Error deleting users'}, 500


@user_ns.route('/export')
class UserExportResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Export users data."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            return {'message': 'Unauthorized'}, 403

        try:
            users = User.query.filter_by(is_deleted=False).all()
            export_data = [user.serialize() for user in users]

            # Add audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='EXPORT',
                resource_type='users',
                resource_id=None,
                details='Exported users data',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'users': export_data}, 200
        except Exception as e:
            logger.error(f"Error exporting users: {str(e)}")
            return {'message': 'Error exporting users'}, 500
