from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.bank_model import Bank
from models.branch_model import Branch
from models.sales_executive_model import SalesExecutive
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

# Define a namespace for dropdown-related operations
dropdown_ns = Namespace('dropdown', description='Dropdown operations')

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'back_office': ['admin', 'manager', 'back_office'],
        'sales_manager': ['admin', 'manager', 'sales_manager']
    }
    return current_user['role'] in roles.get(required_role, [])

# Define response models for Swagger
bank_model = dropdown_ns.model('Bank', {
    'id': fields.Integer(description='Bank ID'),
    'name': fields.String(required=True, description='Bank Name'),
})

branch_model = dropdown_ns.model('Branch', {
    'id': fields.Integer(description='Branch ID'),
    'name': fields.String(required=True, description='Branch Name'),
    'bank_id': fields.Integer(description='Bank ID'),
    'sort_code': fields.String(description='Sort Code'),
})

sales_executive_model = dropdown_ns.model('SalesExecutive', {
    'id': fields.Integer(description='Sales Executive ID'),
    'name': fields.String(required=True, description='Sales Executive Name'),
    'code': fields.String(required=True, description='Sales Executive Code'),
})

impact_product_model = dropdown_ns.model('ImpactProduct', {
    'id': fields.Integer(description='Impact Product ID'),
    'name': fields.String(required=True, description='Impact Product Name'),
    'category': fields.String(required=True, description='Impact Product Category'),
})

@dropdown_ns.route('/')
class DropdownResource(Resource):
    @dropdown_ns.doc(security='Bearer Auth')
    @jwt_required()
    @dropdown_ns.param('type', 'The type of dropdown to retrieve (bank, branch, sales_executive, impact_product)', required=True)
    @dropdown_ns.param('bank_id', 'The bank ID for branch filtering (required for branch dropdown)')
    @dropdown_ns.param('manager_id', 'The manager ID for sales executive filtering (required for sales executive dropdown)')
    @dropdown_ns.param('branch_id', 'The branch ID for sales executive filtering (optional for sales executive dropdown)')
    def get(self):
        """Retrieve dropdown values based on the type."""
        current_user = get_jwt_identity()
        dropdown_type = request.args.get('type')
        response = []

        if not dropdown_type:
            return {"message": "Dropdown type is required"}, 400

        if dropdown_type == 'bank':
            banks = Bank.query.filter_by(is_deleted=False).all()
            response = [bank.serialize() for bank in banks]

        elif dropdown_type == 'branch':
            bank_id = request.args.get('bank_id')
            if not bank_id:
                return {"message": "Bank ID is required for branch dropdown"}, 400
            branches = Branch.query.filter_by(bank_id=bank_id, is_deleted=False).all()
            response = [branch.serialize() for branch in branches]

        elif dropdown_type == 'sales_executive':
            manager_id = request.args.get('manager_id')
            if not manager_id:
                return {"message": "Manager ID is required for sales executive dropdown"}, 400
            branch_id = request.args.get('branch_id')  # Optional: filtering by branch
            query = SalesExecutive.query.filter_by(manager_id=manager_id, is_deleted=False)
            if branch_id:
                query = query.filter_by(branch_id=branch_id)
            sales_executives = query.all()
            response = [se.serialize() for se in sales_executives]

        elif dropdown_type == 'impact_product':
            impact_products = ImpactProduct.query.filter_by(is_deleted=False).all()
            response = [product.serialize() for product in impact_products]

        else:
            return {"message": "Invalid dropdown type"}, 400

        # Log the dropdown access to the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='dropdown',
            resource_id=None,
            details=f"Accessed {dropdown_type} dropdown"
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify(response)
