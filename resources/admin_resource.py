from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.user_model import User, UserStatus, Role
from models.sales_executive_model import SalesExecutive
from models.bank_model import Bank
from models.branch_model import Branch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail, AuditAction
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import json

# Define a namespace for admin-related operations
admin_ns = Namespace('admin', description='Admin operations')

# Define models for Swagger documentation
sales_executive_model = admin_ns.model('SalesExecutive', {
    'id': fields.Integer(description='Sales Executive ID'),
    'name': fields.String(required=True, description='Sales Executive Name'),
    'code': fields.String(required=True, description='Sales Executive Code'),
    'manager_id': fields.Integer(description='Manager ID'),
    'branch_id': fields.Integer(description='Branch ID'),
})

user_status_model = admin_ns.model('UserStatus', {
    'status': fields.String(
        required=True,
        description='User status',
        enum=[s.value for s in UserStatus]
    )
})

user_security_model = admin_ns.model('UserSecurity', {
    'failed_login_attempts': fields.Integer(
        description='Number of failed login attempts'
    ),
    'account_locked_until': fields.DateTime(
        description='Account lock expiration time'
    ),
    'inactivity_timeout': fields.Integer(
        description='Inactivity timeout in minutes'
    )
})

user_activity_model = admin_ns.model('UserActivity', {
    'last_login': fields.DateTime(description='Last login timestamp'),
    'last_activity': fields.DateTime(description='Last activity timestamp'),
    'current_device': fields.String(description='Current device information'),
    'login_history': fields.List(fields.Raw, description='Login history'),
    'device_history': fields.List(fields.Raw, description='Device history')
})

# Simplified models for the resources
bank_model = admin_ns.model('Bank', {
    'id': fields.Integer(),
    'name': fields.String(required=True)
})

branch_model = admin_ns.model('Branch', {
    'id': fields.Integer(),
    'name': fields.String(required=True),
    'bank_id': fields.Integer(),
    'sort_code': fields.String()
})

paypoint_model = admin_ns.model('Paypoint', {
    'id': fields.Integer(),
    'name': fields.String(required=True),
    'location': fields.String()
})

product_model = admin_ns.model('ImpactProduct', {
    'id': fields.Integer(),
    'name': fields.String(required=True),
    'category': fields.String()
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'back_office': ['admin', 'manager', 'back_office'],
        'sales_manager': ['admin', 'manager', 'sales_manager']
    }
    return current_user['role'].lower() in roles.get(required_role, [])

# Helper function to create resources dynamically with validation
def create_resource(data, model_class):
    try:
        resource = model_class(**data)
        db.session.add(resource)
        db.session.commit()
        return resource
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating resource: {e}")
        return None
    except TypeError as e:
        logger.error(f"Type error: {e}")
        return None

# Helper function to update resource fields dynamically
def update_resource(resource, data):
    old_values = {
        key: getattr(resource, key)
        for key in data.keys()
        if hasattr(resource, key)
    }
    for key, value in data.items():
        if hasattr(resource, key):
            setattr(resource, key, value)
    return resource, old_values

# Admin resource class
@admin_ns.route('/')
class AdminResource(Resource):

    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @admin_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    def get(self):
        """Retrieve all data based on the user's role with pagination and audit trail logging."""
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])

        if not user or not user.check_permission('view_admin_dashboard'):
            msg = f"Unauthorized access attempt by user ID {current_user['id']}"
            logger.warning(msg)
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        try:
            users = User.query.filter_by(is_deleted=False).paginate(
                page, per_page, error_out=False
            )
            sales_executives = SalesExecutive.query.filter_by(
                is_deleted=False
            ).paginate(page, per_page, error_out=False)
            banks = Bank.query.filter_by(is_deleted=False).paginate(
                page, per_page, error_out=False
            )
            branches = Branch.query.filter_by(is_deleted=False).paginate(
                page, per_page, error_out=False
            )
            paypoints = Paypoint.query.filter_by(is_deleted=False).paginate(
                page, per_page, error_out=False
            )
            products = ImpactProduct.query.filter_by(is_deleted=False).paginate(
                page, per_page, error_out=False
            )

            # Log the GET action in the audit trail
            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.ACCESS,
                resource_type='admin_dashboard',
                details="Retrieved admin dashboard data",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            logger.info(f"Data retrieved successfully by user ID {current_user['id']}")

            return jsonify({
                'users': [user.serialize() for user in users.items],
                'sales_executives': [se.serialize() for se in sales_executives.items],
                'banks': [bank.serialize() for bank in banks.items],
                'branches': [branch.serialize() for branch in branches.items],
                'paypoints': [paypoint.serialize() for paypoint in paypoints.items],
                'products': [product.serialize() for product in products.items],
                'total_pages': users.pages
            })
        except Exception as e:
            logger.error(f"Error retrieving admin data: {e}")
            return {'message': 'Internal server error'}, 500

    @admin_ns.doc(security='Bearer Auth', responses={201: 'Created', 403: 'Unauthorized'})
    @jwt_required()
    @admin_ns.expect(sales_executive_model, validate=True)
    def post(self):
        """Create new resources (sales_executive, bank, branch, paypoint, or product)."""
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])

        if not user or not user.check_permission('create_resources'):
            msg = f"Unauthorized create attempt by user ID {current_user['id']}"
            logger.warning(msg)
            return {'message': 'Unauthorized'}, 403

        data = request.json
        model_mapping = {
            'sales_executive': SalesExecutive,
            'bank': Bank,
            'branch': Branch,
            'paypoint': Paypoint,
            'product': ImpactProduct
        }

        model_class = model_mapping.get(data.get('type'))
        if not model_class:
            return {'message': f"Invalid resource type '{data.get('type')}'"}, 400

        try:
            resource = create_resource(data, model_class)
            if not resource:
                return {'message': f"Failed to create {data['type']}"}, 500

            # Log the action to audit trail
            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.CREATE,
                resource_type=data['type'],
                resource_id=resource.id,
                new_value=str(data),
                details=f"Created {data['type']} with ID {resource.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            msg = f"{data['type']} created successfully by admin ID {current_user['id']}"
            logger.info(msg)
            return {'message': f"{data['type']} created successfully", 'id': resource.id}, 201
        except Exception as e:
            logger.error(f"Error creating resource: {e}")
            return {'message': 'Internal server error'}, 500

    @admin_ns.doc(security='Bearer Auth', responses={200: 'Updated', 403: 'Unauthorized'})
    @jwt_required()
    def put(self):
        """Update existing resources based on role permissions."""
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        data = request.json

        if not user or not user.check_permission('update_resources'):
            msg = f"Unauthorized update attempt by user ID {current_user['id']}"
            logger.warning(msg)
            return {'message': 'Unauthorized'}, 403

        resource_mapping = {
            'sales_executive': SalesExecutive,
            'bank': Bank,
            'branch': Branch,
            'paypoint': Paypoint,
            'product': ImpactProduct
        }

        try:
            resource = resource_mapping.get(data['type']).query.filter_by(
                id=data['id'], is_deleted=False
            ).first()
            if not resource:
                msg = f"{data['type']} ID {data['id']} not found for update"
                logger.error(msg)
                return {'message': f"{data['type']} not found"}, 404

            resource, old_values = update_resource(resource, data)
            db.session.commit()

            # Log the update to audit trail
            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.UPDATE,
                resource_type=data['type'],
                resource_id=data['id'],
                old_value=str(old_values),
                new_value=str(data),
                details=f"Updated {data['type']} with ID {data['id']}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            msg = f"{data['type']} ID {data['id']} updated by user ID {current_user['id']}"
            logger.info(msg)
            return {'message': f"{data['type']} updated successfully"}, 200
        except Exception as e:
            logger.error(f"Error updating resource: {e}")
            return {'message': 'Internal server error'}, 500

    @admin_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self):
        """Delete resources (Admin only)."""
        current_user = get_jwt_identity()
        user = User.query.get(current_user['id'])
        data = request.json

        if not user or not user.check_permission('delete_resources'):
            msg = f"Unauthorized delete attempt by user ID {current_user['id']}"
            logger.warning(msg)
            return {'message': 'Unauthorized'}, 403

        resource_mapping = {
            'sales_executive': SalesExecutive,
            'bank': Bank,
            'branch': Branch,
            'paypoint': Paypoint,
            'product': ImpactProduct
        }

        try:
            resource = resource_mapping.get(data['type']).query.filter_by(
                id=data['id'], is_deleted=False
            ).first()
            if not resource:
                msg = f"{data['type']} ID {data['id']} not found for deletion"
                logger.error(msg)
                return {'message': f"{data['type']} not found"}, 404

            old_values = resource.serialize()
            resource.is_deleted = True
            db.session.commit()

            # Log the deletion to audit trail
            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.DELETE,
                resource_type=data['type'],
                resource_id=data['id'],
                old_value=str(old_values),
                details=f"Deleted {data['type']} with ID {data['id']}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            msg = f"{data['type']} ID {data['id']} deleted by admin ID {current_user['id']}"
            logger.info(msg)
            return {'message': f"{data['type']} deleted successfully"}, 200
        except Exception as e:
            logger.error(f"Error deleting resource: {e}")
            return {'message': 'Internal server error'}, 500

@admin_ns.route('/users/<int:user_id>/status')
class UserStatusResource(Resource):
    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_ns.expect(user_status_model)
    def put(self, user_id):
        """Update user status."""
        current_user = get_jwt_identity()
        admin = User.query.get(current_user['id'])

        if not admin or not admin.check_permission('manage_users'):
            return {'message': 'Unauthorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        data = request.json
        try:
            user.status = data['status']
            db.session.commit()

            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.UPDATE,
                resource_type='user_status',
                resource_id=user_id,
                new_value=str(data),
                details=f"Updated user status to {data['status']}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            return {'message': 'User status updated successfully'}, 200
        except Exception as e:
            logger.error(f"Error updating user status: {e}")
            return {'message': 'Internal server error'}, 500

@admin_ns.route('/users/<int:user_id>/security')
class UserSecurityResource(Resource):
    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self, user_id):
        """Get user security information."""
        current_user = get_jwt_identity()
        admin = User.query.get(current_user['id'])

        if not admin or not admin.check_permission('view_security_info'):
            return {'message': 'Unauthorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        return {
            'failed_login_attempts': user.failed_login_attempts,
            'account_locked_until': (
                user.account_locked_until.isoformat()
                if user.account_locked_until else None
            ),
            'inactivity_timeout': user.inactivity_timeout
        }, 200

    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_ns.expect(user_security_model)
    def put(self, user_id):
        """Update user security settings."""
        current_user = get_jwt_identity()
        admin = User.query.get(current_user['id'])

        if not admin or not admin.check_permission('manage_security'):
            return {'message': 'Unauthorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        data = request.json
        try:
            if 'failed_login_attempts' in data:
                user.failed_login_attempts = data['failed_login_attempts']
            if 'account_locked_until' in data:
                user.account_locked_until = datetime.fromisoformat(
                    data['account_locked_until']
                )
            if 'inactivity_timeout' in data:
                user.inactivity_timeout = data['inactivity_timeout']

            db.session.commit()

            AuditTrail.log_action(
                user_id=current_user['id'],
                action=AuditAction.UPDATE,
                resource_type='user_security',
                resource_id=user_id,
                new_value=str(data),
                details="Updated user security settings",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            return {'message': 'User security settings updated successfully'}, 200
        except Exception as e:
            logger.error(f"Error updating user security settings: {e}")
            return {'message': 'Internal server error'}, 500

@admin_ns.route('/users/<int:user_id>/activity')
class UserActivityResource(Resource):
    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self, user_id):
        """Get user activity information."""
        current_user = get_jwt_identity()
        admin = User.query.get(current_user['id'])

        if not admin or not admin.check_permission('view_activity_info'):
            return {'message': 'Unauthorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        return {
            'last_login': (
                user.last_login.isoformat() if user.last_login else None
            ),
            'last_activity': (
                user.last_activity.isoformat() if user.last_activity else None
            ),
            'current_device': user.current_device,
            'login_history': (
                json.loads(user.login_history) if user.login_history else []
            ),
            'device_history': (
                json.loads(user.device_history) if user.device_history else []
            )
        }, 200
