from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.user_model import User
from models.sales_executive_model import SalesExecutive
from models.bank_model import Bank
from models.branch_model import Branch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
from sqlalchemy.exc import SQLAlchemyError

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

# Simplified models for the resources
bank_model = admin_ns.model('Bank', {'id': fields.Integer(), 'name': fields.String(required=True)})
branch_model = admin_ns.model('Branch', {'id': fields.Integer(), 'name': fields.String(required=True), 'bank_id': fields.Integer(), 'sort_code': fields.String()})
paypoint_model = admin_ns.model('Paypoint', {'id': fields.Integer(), 'name': fields.String(required=True), 'location': fields.String()})
product_model = admin_ns.model('ImpactProduct', {'id': fields.Integer(), 'name': fields.String(required=True), 'category': fields.String()})

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
    for key, value in data.items():
        if hasattr(resource, key):
            setattr(resource, key, value)
    return resource

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

        if not check_role_permission(current_user, 'back_office'):
            logger.warning(f"Unauthorized access attempt by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        users = User.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        sales_executives = SalesExecutive.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        banks = Bank.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        branches = Branch.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        paypoints = Paypoint.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        products = ImpactProduct.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)

        # Log the GET action in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='GET',
            resource_type='all_resources',
            resource_id=None,
            details=f"Retrieved data for users, sales executives, banks, branches, paypoints, and products.",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

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

    @admin_ns.doc(security='Bearer Auth', responses={201: 'Created', 403: 'Unauthorized'})
    @jwt_required()
    @admin_ns.expect(sales_executive_model, validate=True)
    def post(self):
        """Create new resources (sales_executive, bank, branch, paypoint, or product)."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user, 'admin'):
            logger.warning(f"Unauthorized create attempt by user ID {current_user['id']}")
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

        resource = create_resource(data, model_class)
        if not resource:
            return {'message': f"Failed to create {data['type']}"}, 500

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type=data['type'],
            resource_id=resource.id,
            details=f"Created {data['type']} with details: {data}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"{data['type']} created successfully by admin ID {current_user['id']}")
        return {'message': f"{data['type']} created successfully"}, 201

    @admin_ns.doc(security='Bearer Auth', responses={200: 'Updated', 403: 'Unauthorized'})
    @jwt_required()
    def put(self):
        """Update existing resources based on role permissions."""
        current_user = get_jwt_identity()
        data = request.json

        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized update attempt by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        resource_mapping = {
            'sales_executive': SalesExecutive,
            'bank': Bank,
            'branch': Branch,
            'paypoint': Paypoint,
            'product': ImpactProduct
        }

        resource = resource_mapping.get(data['type']).query.filter_by(id=data['id'], is_deleted=False).first()
        if not resource:
            logger.error(f"{data['type']} ID {data['id']} not found for update")
            return {'message': f"{data['type']} not found"}, 404

        resource = update_resource(resource, data)
        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Updated {data['type']} with details: {data}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"{data['type']} ID {data['id']} updated by user ID {current_user['id']}")
        return {'message': f"{data['type']} updated successfully"}, 200

    @admin_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self):
        """Delete resources (Admin only)."""
        current_user = get_jwt_identity()
        data = request.json

        if not check_role_permission(current_user, 'admin'):
            logger.warning(f"Unauthorized delete attempt by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        resource_mapping = {
            'sales_executive': SalesExecutive,
            'bank': Bank,
            'branch': Branch,
            'paypoint': Paypoint,
            'product': ImpactProduct
        }

        resource = resource_mapping.get(data['type']).query.filter_by(id=data['id'], is_deleted=False).first()
        if not resource:
            logger.error(f"{data['type']} ID {data['id']} not found for deletion")
            return {'message': f"{data['type']} not found"}, 404

        resource.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Deleted {data['type']} with details: {data}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"{data['type']} ID {data['id']} deleted by admin ID {current_user['id']}")
        return {'message': f"{data['type']} deleted successfully"}, 200
