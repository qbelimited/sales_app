from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.user_model import User
from models.sales_executive_model import SalesExecutive
from models.bank_model import Bank
from models.branch_model import Branch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail
from models.under_investigation_model import UnderInvestigation
from app import db
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

bank_model = admin_ns.model('Bank', {
    'id': fields.Integer(description='Bank ID'),
    'name': fields.String(required=True, description='Bank Name'),
})

branch_model = admin_ns.model('Branch', {
    'id': fields.Integer(description='Branch ID'),
    'name': fields.String(required=True, description='Branch Name'),
    'bank_id': fields.Integer(description='Bank ID'),
    'sort_code': fields.String(description='Sort Code'),
})

paypoint_model = admin_ns.model('Paypoint', {
    'id': fields.Integer(description='Paypoint ID'),
    'name': fields.String(required=True, description='Paypoint Name'),
    'location': fields.String(description='Paypoint Location'),
})

product_model = admin_ns.model('ImpactProduct', {
    'id': fields.Integer(description='Product ID'),
    'name': fields.String(required=True, description='Product Name'),
    'category': fields.String(description='Product Category'),
})

# Helper function to check permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'back_office': ['admin', 'manager', 'back_office'],
        'sales_manager': ['admin', 'manager', 'sales_manager']
    }
    return current_user['role'] in roles.get(required_role, [])

# Admin resource class
@admin_ns.route('/')
class AdminResource(Resource):
    @admin_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Retrieve all data based on the user's role."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user, 'back_office'):
            return {'message': 'Unauthorized'}, 403

        users = User.query.filter_by(is_deleted=False).all()
        sales_executives = SalesExecutive.query.filter_by(is_deleted=False).all()
        banks = Bank.query.filter_by(is_deleted=False).all()
        branches = Branch.query.filter_by(is_deleted=False).all()
        paypoints = Paypoint.query.filter_by(is_deleted=False).all()
        products = ImpactProduct.query.filter_by(is_deleted=False).all()

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
            return {'message': 'Unauthorized'}, 403

        data = request.json
        if data['type'] == 'sales_executive':
            new_sales_executive = SalesExecutive(
                name=data['name'],
                code=data['code'],
                manager_id=data['manager_id'],
                branch_id=data['branch_id']
            )
            db.session.add(new_sales_executive)
        elif data['type'] == 'bank':
            new_bank = Bank(name=data['name'])
            db.session.add(new_bank)
        elif data['type'] == 'branch':
            new_branch = Branch(
                name=data['name'],
                bank_id=data.get('bank_id'),
                sort_code=data.get('sort_code')
            )
            db.session.add(new_branch)
        elif data['type'] == 'paypoint':
            new_paypoint = Paypoint(name=data['name'], location=data['location'])
            db.session.add(new_paypoint)
        elif data['type'] == 'product':
            new_product = ImpactProduct(name=data['name'], category=data['category'])
            db.session.add(new_product)
        db.session.commit()

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type=data['type'],
            resource_id=new_sales_executive.id if data['type'] == 'sales_executive' else (
                new_bank.id if data['type'] == 'bank' else (
                    new_branch.id if data['type'] == 'branch' else (
                        new_paypoint.id if data['type'] == 'paypoint' else new_product.id))),
            details=f"Created {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Resource added successfully'}, 201

    @admin_ns.doc(security='Bearer Auth', responses={200: 'Updated', 403: 'Unauthorized'})
    @jwt_required()
    def put(self):
        """Update existing resources based on role permissions."""
        current_user = get_jwt_identity()
        data = request.json

        if not check_role_permission(current_user, 'manager'):
            return {'message': 'Unauthorized'}, 403

        if data['type'] == 'sales_executive':
            se = SalesExecutive.query.filter_by(id=data['id'], is_deleted=False).first()
            if not se:
                return {'message': 'Sales Executive not found'}, 404
            se.name = data.get('name', se.name)
            se.code = data.get('code', se.code)
            se.manager_id = data.get('manager_id', se.manager_id)
            se.branch_id = data.get('branch_id', se.branch_id)
        elif data['type'] == 'bank':
            bank = Bank.query.filter_by(id=data['id'], is_deleted=False).first()
            if not bank:
                return {'message': 'Bank not found'}, 404
            bank.name = data.get('name', bank.name)
        elif data['type'] == 'branch':
            branch = Branch.query.filter_by(id=data['id'], is_deleted=False).first()
            if not branch:
                return {'message': 'Branch not found'}, 404
            branch.name = data.get('name', branch.name)
            branch.bank_id = data.get('bank_id', branch.bank_id)
            branch.sort_code = data.get('sort_code', branch.sort_code)
        elif data['type'] == 'paypoint':
            paypoint = Paypoint.query.filter_by(id=data['id'], is_deleted=False).first()
            if not paypoint:
                return {'message': 'Paypoint not found'}, 404
            paypoint.name = data.get('name', paypoint.name)
            paypoint.location = data.get('location', paypoint.location)
        elif data['type'] == 'product':
            product = ImpactProduct.query.filter_by(id=data['id'], is_deleted=False).first()
            if not product:
                return {'message': 'Product not found'}, 404
            product.name = data.get('name', product.name)
            product.category = data.get('category', product.category)
        db.session.commit()

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Updated {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Resource updated successfully'}, 200

    @admin_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self):
        """Delete resources (Admin only)."""
        current_user = get_jwt_identity()
        data = request.json

        if not check_role_permission(current_user, 'admin'):
            return {'message': 'Unauthorized'}, 403

        if data['type'] == 'sales_executive':
            se = SalesExecutive.query.filter_by(id=data['id'], is_deleted=False).first()
            if not se:
                return {'message': 'Sales Executive not found'}, 404
            se.is_deleted = True
        elif data['type'] == 'bank':
            bank = Bank.query.filter_by(id=data['id'], is_deleted=False).first()
            if not bank:
                return {'message': 'Bank not found'}, 404
            bank.is_deleted = True
        elif data['type'] == 'branch':
            branch = Branch.query.filter_by(id=data['id'], is_deleted=False).first()
            if not branch:
                return {'message': 'Branch not found'}, 404
            branch.is_deleted = True
        elif data['type'] == 'paypoint':
            paypoint = Paypoint.query.filter_by(id=data['id'], is_deleted=False).first()
            if not paypoint:
                return {'message': 'Paypoint not found'}, 404
            paypoint.is_deleted = True
        elif data['type'] == 'product':
            product = ImpactProduct.query.filter_by(id=data['id'], is_deleted=False).first()
            if not product:
                return {'message': 'Product not found'}, 404
            product.is_deleted = True
        db.session.commit()

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Deleted {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Resource deleted successfully'}, 200
