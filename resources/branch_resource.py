from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.branch_model import Branch
from models.audit_model import AuditTrail
from app import db, logger  # Import the logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for branch-related operations
branch_ns = Namespace('branch', description='Branch operations')

# Define a model for the branch in Swagger documentation
branch_model = branch_ns.model('Branch', {
    'id': fields.Integer(description='Branch ID'),
    'name': fields.String(required=True, description='Branch Name'),
    'sort_code': fields.String(description='Sort Code'),
    'ghpost_gps': fields.String(description='GPS Address')
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'back_office': ['admin', 'manager', 'back_office'],
        'sales_manager': ['admin', 'manager', 'sales_manager']
    }
    return current_user['role'] in roles.get(required_role, [])

@branch_ns.route('/')
class BranchListResource(Resource):
    @branch_ns.doc(security='Bearer Auth')
    @jwt_required()
    @branch_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @branch_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @branch_ns.param('filter_by', 'Filter by branch name', type='string')
    @branch_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of branches (view rights for all roles)."""
        current_user = get_jwt_identity()

        # Check if the user has permission to view branches
        if not check_role_permission(current_user, 'back_office'):
            logger.warning(f"Unauthorized attempt to view branches by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        branch_query = Branch.query.filter_by(is_deleted=False)

        if filter_by:
            branch_query = branch_query.filter(Branch.name.ilike(f'%{filter_by}%'))

        try:
            branches = branch_query.order_by(getattr(Branch, sort_by).desc()).paginate(page, per_page, error_out=False)
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
        """Create a new branch (admin and manager only)."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized attempt to create a branch by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validation of required fields
        if not data.get('name'):
            logger.error(f"Branch creation failed due to missing name by user {current_user['id']}")
            return {'message': 'Missing required fields'}, 400

        new_branch = Branch(
            name=data['name'],
            ghpost_gps=data.get('ghpost_gps'),
            sort_code=data.get('sort_code')
        )
        db.session.add(new_branch)
        db.session.commit()

        # Log creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='branch',
            resource_id=new_branch.id,
            details=f"Created branch with details: {data}"
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
        """Retrieve a specific branch by ID (view rights for all roles)."""
        current_user = get_jwt_identity()

        # Check if the user has permission to view the branch
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
        """Update an existing branch (admin and manager only)."""
        current_user = get_jwt_identity()

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
        branch.sort_code = data.get('sort_code', branch.sort_code)
        branch.updated_at = datetime.utcnow()

        db.session.commit()

        # Log update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Updated branch with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch {branch_id} updated successfully by user {current_user['id']}")
        return branch.serialize(), 200

    @branch_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Branch not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, branch_id):
        """Soft-delete a branch (admin only)."""
        current_user = get_jwt_identity()

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
            details=f"Deleted branch with id: {branch_id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch {branch_id} deleted successfully by user {current_user['id']}")
        return {'message': 'Branch deleted successfully'}, 200
