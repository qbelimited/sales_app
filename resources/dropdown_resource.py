from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.bank_model import Bank
from models.branch_model import Branch
from models.sales_executive_model import SalesExecutive
from models.impact_product_model import ImpactProduct
from models.user_model import User
from models.audit_model import AuditTrail
from app import db, logger  # Import logger for logging
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
    return current_user['role'].lower() in roles.get(required_role, [])

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

sales_manager_model = dropdown_ns.model('SalesManager', {
    'id': fields.Integer(description='User ID'),
    'name': fields.String(required=True, description='Sales Manager Name'),
    'email': fields.String(description='Sales Manager Email')
})

# Extend the Dropdown API for additional dropdowns
@dropdown_ns.route('/')
class DropdownResource(Resource):
    @dropdown_ns.doc(security='Bearer Auth')
    @jwt_required()
    @dropdown_ns.param('type', 'The type of dropdown to retrieve (bank, branch, sales_executive, impact_product, sales_manager)', required=True)
    @dropdown_ns.param('bank_id', 'The bank ID for branch filtering (required for branch dropdown)', type='integer')
    @dropdown_ns.param('manager_id', 'The manager ID for sales executive filtering (required for sales executive dropdown)', type='integer')
    @dropdown_ns.param('branch_id', 'The branch ID for sales executive filtering (optional for sales executive dropdown)', type='integer')
    @dropdown_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @dropdown_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    def get(self):
        """Retrieve dropdown values based on the type."""
        current_user = get_jwt_identity()  # Fetch current user from JWT
        dropdown_type = request.args.get('type')  # Fetch dropdown type from query parameter
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        if not dropdown_type:
            logger.error("Dropdown type is missing")
            return {"message": "Dropdown type is required"}, 400

        try:
            if dropdown_type == 'bank':
                return self.get_banks(page, per_page)
            elif dropdown_type == 'branch':
                bank_id = request.args.get('bank_id')
                if not bank_id:
                    return {"message": "Bank ID is required for branch dropdown"}, 400
                return self.get_branches(bank_id, page, per_page)
            elif dropdown_type == 'sales_executive':
                manager_id = request.args.get('manager_id')
                if not manager_id:
                    return {"message": "Manager ID is required for sales executive dropdown"}, 400
                branch_id = request.args.get('branch_id')  # Optional filter
                return self.get_sales_executives(manager_id, branch_id, page, per_page)
            elif dropdown_type == 'impact_product':
                return self.get_impact_products(page, per_page)
            elif dropdown_type == 'sales_manager':
                return self.get_sales_managers(page, per_page)
            else:
                logger.error(f"Invalid dropdown type: {dropdown_type}")
                return {"message": "Invalid dropdown type"}, 400
        except Exception as e:
            logger.error(f"Error retrieving {dropdown_type} dropdown: {e}")
            return {"message": f"Error retrieving {dropdown_type} dropdown"}, 500

    def get_banks(self, page, per_page):
        """Retrieve banks for dropdown."""
        banks = Bank.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        logger.info(f"Banks retrieved for dropdown, total: {banks.total}")
        return jsonify([bank.serialize() for bank in banks.items])

    def get_branches(self, bank_id, page, per_page):
        """Retrieve branches for dropdown."""
        branches = Branch.query.filter_by(bank_id=bank_id, is_deleted=False).paginate(page, per_page, error_out=False)
        logger.info(f"Branches retrieved for bank ID {bank_id}, total: {branches.total}")
        return jsonify([branch.serialize() for branch in branches.items])

    def get_sales_executives(self, manager_id, branch_id, page, per_page):
        """Retrieve sales executives for dropdown."""
        query = SalesExecutive.query.filter_by(manager_id=manager_id, is_deleted=False)
        if branch_id:
            query = query.filter_by(branch_id=branch_id)
        sales_executives = query.paginate(page=page, per_page=per_page, error_out=False)
        logger.info(f"Sales executives retrieved for manager ID {manager_id}, total: {sales_executives.total}")
        return jsonify([se.serialize() for se in sales_executives.items])

    def get_impact_products(self, page, per_page):
        """Retrieve impact products for dropdown."""
        products = ImpactProduct.query.filter_by(is_deleted=False).paginate(page, per_page, error_out=False)
        logger.info(f"Impact products retrieved for dropdown, total: {products.total}")
        return jsonify([product.serialize() for product in products.items])

    def get_sales_managers(self, page, per_page):
        """Retrieve sales managers (users with role 'sales_manager') for dropdown."""
        sales_managers = User.query.filter_by(role_id='sales_manager', is_deleted=False).paginate(page, per_page, error_out=False)
        logger.info(f"Sales managers retrieved for dropdown, total: {sales_managers.total}")
        return jsonify([{'id': manager.id, 'name': manager.name, 'email': manager.email} for manager in sales_managers.items])

    # Log the dropdown access to the audit trail
    def log_audit(self, current_user, dropdown_type):
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='dropdown',
            resource_id=None,
            details=f"Accessed {dropdown_type} dropdown"
        )
        db.session.add(audit)
        db.session.commit()
