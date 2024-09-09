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
    return current_user['role'] in roles.get(required_role, [])

# Helper function to create resources dynamically
def create_resource(data, model_class):
    try:
        resource = model_class(**data)
        db.session.add(resource)
        db.session.commit()
        return resource
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating resource: {e}")
        return None

# Admin resource class
@admin_ns.route('/')
class AdminResource(Resource):
    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Retrieve all data based on the user's role."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user, 'back_office'):
            logger.warning(f"Unauthorized access attempt by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        # Fetch all data
        users = User.query.filter_by(is_deleted=False).all()
        sales_executives = SalesExecutive.query.filter_by(is_deleted=False).all()
        banks = Bank.query.filter_by(is_deleted=False).all()
        branches = Branch.query.filter_by(is_deleted=False).all()
        paypoints = Paypoint.query.filter_by(is_deleted=False).all()
        products = ImpactProduct.query.filter_by(is_deleted=False).all()

        logger.info(f"Data retrieved successfully by user ID {current_user['id']}")
        return jsonify({
            'users': [user.serialize() for user in users],
            'sales_executives': [se.serialize() for se in sales_executives],
            'banks': [bank.serialize() for bank in banks],
            'branches': [branch.serialize() for branch in branches],
            'paypoints': [paypoint.serialize() for paypoint in paypoints],
            'products': [product.serialize() for product in products]
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

        resource = create_resource(data, model_mapping.get(data['type']))
        if not resource:
            return {'message': f"Failed to create {data['type']}"}, 500

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type=data['type'],
            resource_id=resource.id,
            details=f"Created {data['type']} with details: {data}"
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

        for key, value in data.items():
            if hasattr(resource, key):
                setattr(resource, key, value)

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Updated {data['type']} with details: {data}"
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
            details=f"Deleted {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"{data['type']} ID {data['id']} deleted by admin ID {current_user['id']}")
        return {'message': f"{data['type']} deleted successfully"}, 200
