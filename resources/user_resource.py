from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import User
from models.user_session_model import UserSession
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

# Define a namespace for User-related operations
user_ns = Namespace('user', description='User operations')

# Define models for Swagger documentation
user_model = user_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(required=True, description='User Email'),
    'name': fields.String(required=True, description='User Name'),
    'role_id': fields.Integer(required=True, description='Role ID'),
    'is_active': fields.Boolean(description='Is Active'),
    'is_deleted': fields.Boolean(description='Is Deleted'),
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
            details=f"User accessed list of users"
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

        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to create a new user.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        new_user = User(
            email=data['email'],
            name=data['name'],
            role_id=data['role_id']
        )
        new_user.set_password(data['password'])  # Assuming you have a method to hash the password

        db.session.add(new_user)
        db.session.commit()

        # Log the creation to audit trail and logger
        logger.info(f"User {current_user['id']} created a new user with ID {new_user.id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='user',
            resource_id=new_user.id,
            details=f"User created a new User with ID {new_user.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_user.serialize(), 201


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
            details=f"User accessed details of User with ID {user_id}"
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
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized update attempt by User {current_user['id']} on User {user_id}.")
            return {'message': 'Unauthorized'}, 403

        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            logger.error(f"User with ID {user_id} not found for update by User {current_user['id']}.")
            return {'message': 'User not found'}, 404

        data = request.json
        user.email = data.get('email', user.email)
        user.name = data.get('name', user.name)
        user.role_id = data.get('role_id', user.role_id)
        user.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail and logger
        logger.info(f"User {current_user['id']} updated User {user_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='user',
            resource_id=user.id,
            details=f"User updated User with ID {user.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return user.serialize(), 200

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
            details=f"User deleted User with ID {user.id}"
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
            details=f"User updated password"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Password updated successfully'}, 200

# User Sessions Management
@user_ns.route('/<int:user_id>/sessions')
class UserSessionResource(Resource):
    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.marshal_list_with(session_model)
    def get(self, user_id):
        """Retrieve active sessions for a specific user."""
        current_user = get_jwt_identity()

        # Retrieve active sessions for the specified user
        sessions = UserSession.get_active_sessions(user_id=user_id)

        # Log the access to the sessions
        logger.info(f"User {current_user['id']} accessed sessions of user {user_id}.")

        # Add audit trail entry
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='user_sessions',
            resource_id=user_id,
            details=f"Accessed active sessions for user {user_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return [session.serialize() for session in sessions], 200

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.expect(session_model, validate=True)
    def post(self, user_id):
        """Create a new session for a user."""
        current_user = get_jwt_identity()

        # Only admin or the user themselves can create a session
        if current_user['id'] != user_id and current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.json

        new_session = UserSession(
            user_id=user_id,
            ip_address=data.get('ip_address', '0.0.0.0'),  # Default to '0.0.0.0' if not provided
            login_time=datetime.utcnow(),
            is_active=True,
            expires_at=datetime.utcnow() + timedelta(minutes=45),  # Default to 45 minutes
        )
        db.session.add(new_session)
        db.session.commit()

        logger.info(f"User {current_user['id']} created a new session for user {user_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='session',
            resource_id=new_session.id,
            details=f"Created session for user {user_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_session.serialize(), 201

    @user_ns.doc(security='Bearer Auth')
    @jwt_required()
    @user_ns.response(200, 'Session deleted successfully')
    @user_ns.response(404, 'Session not found')
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

        # Log the action to the logger
        logger.info(f"User {current_user['id']} ended all active sessions for user {user_id}.")

        # Add audit trail entry
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='user_sessions',
            resource_id=user_id,
            details=f"Ended all active sessions for user {user_id}"
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
