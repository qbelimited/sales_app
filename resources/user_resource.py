from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.user_model import User
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for User-related operations
user_ns = Namespace('user', description='User operations')

# Define models for Swagger documentation
user_model = user_ns.model('User', {
    'id': fields.Integer(description='User ID'),
    'email': fields.String(required=True, description='User Email'),
    'name': fields.String(required=True, description='User Name'),
    'role_id': fields.Integer(required=True, description='Role ID'),
    'microsoft_id': fields.String(description='Microsoft ID')
})

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

        users = user_query.order_by(sort_by).paginate(page, per_page, error_out=False)

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

        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to create a new user.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        new_user = User(
            email=data['email'],
            name=data['name'],
            role_id=data['role_id'],
            microsoft_id=data.get('microsoft_id')
        )
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
    @user_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'User not found', 403: 'Unauthorized'})
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
        """Update an existing User (admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
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
        if current_user['role'] != 'admin':
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
