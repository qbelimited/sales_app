from app import db
from datetime import datetime
from flask_restx import Namespace, Resource, fields
from flask import request
from models.branch_model import Branch
from models.audit_model import AuditTrail
from app import logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip

# Define a namespace for branch-related operations
branch_ns = Namespace('branch', description='Branch operations')

# Define a model for the branch in Swagger documentation
branch_model = branch_ns.model('Branch', {
    'id': fields.Integer(description='Branch ID'),
    'name': fields.String(required=True, description='Branch Name'),
    'ghpost_gps': fields.String(description='GhPost GPS Address'),
    'address': fields.String(description='Branch Address'),
    'city': fields.String(description='Branch City'),
    'region': fields.String(description='Branch Region')
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

@branch_ns.route('/')
class BranchListResource(Resource):
    @branch_ns.doc(security='Bearer Auth')
    @jwt_required()
    @branch_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @branch_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @branch_ns.param('filter_by', 'Filter by branch name', type='string')
    @branch_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of branches."""
        current_user = get_jwt_identity()

        # Check role permissions
        if not check_role_permission(current_user, 'back_office'):
            logger.warning(f"Unauthorized attempt to view branches by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        # Pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        branch_query = Branch.query.filter_by(is_deleted=False)

        if filter_by:
            branch_query = branch_query.filter(Branch.name.ilike(f'%{filter_by}%'))

        try:
            branches = branch_query.order_by(getattr(Branch, sort_by).desc()).paginate(page=page, per_page=per_page, error_out=False)
        except AttributeError:
            logger.error(f"Invalid sort_by field: {sort_by}")
            return {'message': 'Invalid sorting field'}, 400

        logger.info(f"Branches retrieved successfully by user {current_user['id']}")
        return {
            'branches': [branch.serialize() for branch in branches.items],
            'total': branches.total,
            'pages': branches.pages,
            'current_page': branches.page
        }, 200

    @branch_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Missing required fields', 403: 'Unauthorized'})
    @jwt_required()
    @branch_ns.expect(branch_model, validate=True)
    def post(self):
        """Create a new branch."""
        current_user = get_jwt_identity()

        # Check role permissions
        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized attempt to create a branch by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validation
        if not data.get('name'):
            logger.error(f"Branch creation failed due to missing name by user {current_user['id']}")
            return {'message': 'Branch name is required'}, 400

        new_branch = Branch(
            name=data['name'],
            ghpost_gps=data.get('ghpost_gps'),
            address=data.get('address'),
            city=data.get('city'),
            region=data.get('region')
        )
        db.session.add(new_branch)
        db.session.commit()

        # Log creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='branch',
            resource_id=new_branch.id,
            details=f"Created branch with details: {data}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch '{new_branch.name}' created successfully by user {current_user['id']}")
        return new_branch.serialize(), 201

@branch_ns.route('/<int:branch_id>')
class BranchResource(Resource):
    @branch_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Branch not found', 403: 'Unauthorized'})
    @jwt_required()
    def get(self, branch_id):
        """Retrieve a specific branch by ID."""
        current_user = get_jwt_identity()

        # Check role permissions
        if not check_role_permission(current_user, 'back_office'):
            logger.warning(f"Unauthorized attempt to view branch {branch_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
        if not branch:
            logger.error(f"Branch {branch_id} not found by user {current_user['id']}")
            return {'message': 'Branch not found'}, 404

        logger.info(f"Branch {branch_id} retrieved successfully by user {current_user['id']}")
        return branch.serialize(), 200

    @branch_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Branch not found', 403: 'Unauthorized'})
    @jwt_required()
    @branch_ns.expect(branch_model, validate=True)
    def put(self, branch_id):
        """Update an existing branch."""
        current_user = get_jwt_identity()

        # Check role permissions
        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized attempt to update branch {branch_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
        if not branch:
            logger.error(f"Branch {branch_id} not found for update by user {current_user['id']}")
            return {'message': 'Branch not found'}, 404

        data = request.json
        branch.name = data.get('name', branch.name)
        branch.ghpost_gps = data.get('ghpost_gps', branch.ghpost_gps)
        branch.address = data.get('address', branch.address)
        branch.city = data.get('city', branch.city)
        branch.region = data.get('region', branch.region)
        branch.updated_at = datetime.utcnow()

        db.session.commit()

        # Log update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Updated branch with details: {data}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch {branch_id} updated successfully by user {current_user['id']}")
        return branch.serialize(), 200

    @branch_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Branch not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, branch_id):
        """Soft-delete a branch."""
        current_user = get_jwt_identity()

        # Check role permissions
        if not check_role_permission(current_user, 'admin'):
            logger.warning(f"Unauthorized attempt to delete branch {branch_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
        if not branch:
            logger.error(f"Branch {branch_id} not found for deletion by user {current_user['id']}")
            return {'message': 'Branch not found'}, 404

        branch.is_deleted = True
        db.session.commit()

        # Log deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Deleted branch with id: {branch_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch {branch_id} deleted successfully by user {current_user['id']}")
        return {'message': 'Branch deleted successfully'}, 200
