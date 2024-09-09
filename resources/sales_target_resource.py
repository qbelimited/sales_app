from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive
from models.user_model import User
from models.performance_model import SalesTarget
from models.audit_model import AuditTrail
from app import db, logger  # Import logger from app.py
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for Sales Target operations
sales_target_ns = Namespace('sales_target', description='Sales Target operations')

# Define model for Swagger documentation
sales_target_model = sales_target_ns.model('SalesTarget', {
    'id': fields.Integer(description='Sales Target ID'),
    'sales_executive_id': fields.Integer(required=True, description='Sales Executive ID'),
    'sales_manager_id': fields.Integer(required=True, description='Sales Manager ID'),
    'target_sales_count': fields.Integer(required=True, description='Target number of sales'),
    'target_premium_amount': fields.Float(required=True, description='Target premium amount')
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager']
    }
    return current_user['role'].lower() in roles.get(required_role, [])

@sales_target_ns.route('/')
class SalesTargetListResource(Resource):
    @sales_target_ns.doc(security='Bearer Auth')
    @jwt_required()
    @sales_target_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @sales_target_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @sales_target_ns.param('filter_by', 'Filter by sales executive name', type='string')
    @sales_target_ns.param('sort_by', 'Sort by field (e.g., created_at)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of Sales Targets."""
        current_user = get_jwt_identity()

        # Pagination and filtering params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        sales_target_query = SalesTarget.query

        if filter_by:
            sales_target_query = sales_target_query.join(SalesExecutive).filter(SalesExecutive.name.ilike(f'%{filter_by}%'))

        sales_targets = sales_target_query.order_by(getattr(SalesTarget, sort_by).desc()).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_target_list',
            resource_id=None,
            details="User accessed list of Sales Targets"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales targets retrieved by user {current_user['id']}")

        return {
            'sales_targets': [target.serialize() for target in sales_targets.items],
            'total': sales_targets.total,
            'pages': sales_targets.pages,
            'current_page': sales_targets.page
        }, 200

    @sales_target_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Missing required fields', 403: 'Unauthorized'})
    @jwt_required()
    @sales_target_ns.expect(sales_target_model, validate=True)
    def post(self):
        """Create a new Sales Target (admin and manager only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized attempt to create sales target by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validation of required fields
        if not data.get('sales_executive_id') or not data.get('sales_manager_id'):
            logger.error(f"Sales target creation failed due to missing fields by user {current_user['id']}")
            return {'message': 'Missing required fields'}, 400

        new_target = SalesTarget(
            sales_executive_id=data['sales_executive_id'],
            sales_manager_id=data['sales_manager_id'],
            target_sales_count=data['target_sales_count'],
            target_premium_amount=data['target_premium_amount']
        )
        db.session.add(new_target)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sales_target',
            resource_id=new_target.id,
            details=f"Created new Sales Target for Sales Executive ID {new_target.sales_executive_id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales target created for Sales Executive ID {new_target.sales_executive_id} by user {current_user['id']}")

        return new_target.serialize(), 201

@sales_target_ns.route('/<int:target_id>')
class SalesTargetResource(Resource):
    @sales_target_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Sales Target not found', 403: 'Unauthorized'})
    @jwt_required()
    def get(self, target_id):
        """Retrieve a specific Sales Target by ID."""
        current_user = get_jwt_identity()

        target = SalesTarget.query.filter_by(id=target_id).first()
        if not target:
            logger.error(f"Sales target ID {target_id} not found by user {current_user['id']}")
            return {'message': 'Sales Target not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_target',
            resource_id=target_id,
            details=f"User accessed Sales Target with ID {target_id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales target ID {target_id} retrieved by user {current_user['id']}")

        return target.serialize(), 200

    @sales_target_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Sales Target not found', 403: 'Unauthorized'})
    @jwt_required()
    @sales_target_ns.expect(sales_target_model, validate=True)
    def put(self, target_id):
        """Update an existing Sales Target (admin and manager only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized attempt to update sales target ID {target_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        target = SalesTarget.query.filter_by(id=target_id).first()
        if not target:
            logger.error(f"Sales target ID {target_id} not found for update by user {current_user['id']}")
            return {'message': 'Sales Target not found'}, 404

        data = request.json
        target.sales_executive_id = data.get('sales_executive_id', target.sales_executive_id)
        target.sales_manager_id = data.get('sales_manager_id', target.sales_manager_id)
        target.target_sales_count = data.get('target_sales_count', target.target_sales_count)
        target.target_premium_amount = data.get('target_premium_amount', target.target_premium_amount)
        target.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_target',
            resource_id=target.id,
            details=f"Updated Sales Target with ID {target.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales target ID {target_id} updated by user {current_user['id']}")

        return target.serialize(), 200

    @sales_target_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Sales Target not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, target_id):
        """Soft-delete a Sales Target (admin only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'admin'):
            logger.warning(f"Unauthorized attempt to delete sales target ID {target_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        target = SalesTarget.query.filter_by(id=target_id).first()
        if not target:
            logger.error(f"Sales target ID {target_id} not found for deletion by user {current_user['id']}")
            return {'message': 'Sales Target not found'}, 404

        target.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='sales_target',
            resource_id=target.id,
            details=f"Deleted Sales Target with ID {target.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales target ID {target_id} deleted by user {current_user['id']}")

        return {'message': 'Sales Target deleted successfully'}, 200
