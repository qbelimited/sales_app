from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.performance_model import SalesPerformance
from models.audit_model import AuditTrail
from models.performance_model import SalesTarget
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for sales performance-related operations
sales_performance_ns = Namespace('sales_performance', description='Sales Performance operations')

# Define models for Swagger documentation
sales_performance_model = sales_performance_ns.model('SalesPerformance', {
    'id': fields.Integer(description='Sales Performance ID'),
    'sales_executive_id': fields.Integer(required=True, description='Sales Executive ID'),
    'sales_manager_id': fields.Integer(description='Sales Manager ID'),
    'actual_sales_count': fields.Integer(required=True, description='Actual number of sales made'),
    'actual_premium_amount': fields.Float(required=True, description='Actual premium amount sold'),
    'target_id': fields.Integer(description='Sales Target ID'),
    'performance_date': fields.DateTime(description='Performance date'),
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'sales_manager': ['admin', 'manager', 'sales_manager']
    }
    return current_user['role'] in roles.get(required_role, [])

@sales_performance_ns.route('/')
class SalesPerformanceResource(Resource):
    @sales_performance_ns.doc(security='Bearer Auth')
    @jwt_required()
    @sales_performance_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @sales_performance_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @sales_performance_ns.param('sales_executive_id', 'Filter by Sales Executive ID', type='integer')
    @sales_performance_ns.param('sales_manager_id', 'Filter by Sales Manager ID', type='integer')
    @sales_performance_ns.param('target_id', 'Filter by Sales Target ID', type='integer')
    def get(self):
        """Retrieve sales performance records with pagination."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'sales_manager'):
            logger.warning(f"Unauthorized access attempt by User ID {current_user['id']} to retrieve sales performances.")
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sales_executive_id = request.args.get('sales_executive_id')
        sales_manager_id = request.args.get('sales_manager_id')
        target_id = request.args.get('target_id')

        # Build query based on filters
        sales_performance_query = SalesPerformance.query.filter_by(is_deleted=False)
        if sales_executive_id:
            sales_performance_query = sales_performance_query.filter_by(sales_executive_id=sales_executive_id)
        if sales_manager_id:
            sales_performance_query = sales_performance_query.filter_by(sales_manager_id=sales_manager_id)
        if target_id:
            sales_performance_query = sales_performance_query.filter_by(target_id=target_id)

        sales_performances = sales_performance_query.paginate(page, per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_performance_list',
            resource_id=None,
            details="User accessed sales performance records"
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'sales_performances': [sp.serialize() for sp in sales_performances.items],
            'total': sales_performances.total,
            'pages': sales_performances.pages,
            'current_page': sales_performances.page,
            'has_next': sales_performances.has_next,
            'has_prev': sales_performances.has_prev
        })

    @sales_performance_ns.doc(security='Bearer Auth', responses={201: 'Created', 403: 'Unauthorized'})
    @jwt_required()
    @sales_performance_ns.expect(sales_performance_model, validate=True)
    def post(self):
        """Create a new sales performance record (for managers or sales managers only)."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'sales_manager'):
            logger.warning(f"Unauthorized sales performance creation attempt by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate the target ID exists
        target = SalesTarget.query.filter_by(id=data['target_id'], is_deleted=False).first()
        if not target:
            logger.error(f"Sales Target ID {data['target_id']} not found.")
            return {'message': 'Sales Target not found'}, 404

        new_sales_performance = SalesPerformance(
            sales_executive_id=data['sales_executive_id'],
            sales_manager_id=data.get('sales_manager_id', current_user['id']),
            actual_sales_count=data['actual_sales_count'],
            actual_premium_amount=data['actual_premium_amount'],
            target_id=data['target_id'],
            performance_date=data.get('performance_date', datetime.utcnow())
        )
        db.session.add(new_sales_performance)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sales_performance',
            resource_id=new_sales_performance.id,
            details=f"Sales manager created a new sales performance with ID {new_sales_performance.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales Performance created by User ID {current_user['id']} with Performance ID {new_sales_performance.id}.")
        return new_sales_performance.serialize(), 201

@sales_performance_ns.route('/<int:performance_id>')
class SingleSalesPerformanceResource(Resource):
    @sales_performance_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Sales Performance not found', 403: 'Unauthorized'})
    @jwt_required()
    def get(self, performance_id):
        """Retrieve a specific sales performance by its ID."""
        current_user = get_jwt_identity()
        sales_performance = SalesPerformance.query.filter_by(id=performance_id, is_deleted=False).first()

        if not sales_performance:
            logger.error(f"Sales Performance ID {performance_id} not found.")
            return {'message': 'Sales Performance not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_performance',
            resource_id=performance_id,
            details=f"User accessed Sales Performance with ID {performance_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return sales_performance.serialize(), 200

    @sales_performance_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Sales Performance not found', 403: 'Unauthorized'})
    @jwt_required()
    @sales_performance_ns.expect(sales_performance_model, validate=True)
    def put(self, performance_id):
        """Update an existing sales performance record."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'sales_manager'):
            logger.warning(f"Unauthorized update attempt by User ID {current_user['id']} on Sales Performance ID {performance_id}.")
            return {'message': 'Unauthorized'}, 403

        sales_performance = SalesPerformance.query.filter_by(id=performance_id, is_deleted=False).first()
        if not sales_performance:
            logger.error(f"Sales Performance ID {performance_id} not found for update.")
            return {'message': 'Sales Performance not found'}, 404

        data = request.json
        sales_performance.actual_sales_count = data.get('actual_sales_count', sales_performance.actual_sales_count)
        sales_performance.actual_premium_amount = data.get('actual_premium_amount', sales_performance.actual_premium_amount)
        sales_performance.performance_date = data.get('performance_date', sales_performance.performance_date)
        sales_performance.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_performance',
            resource_id=sales_performance.id,
            details=f"User updated Sales Performance with ID {sales_performance.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales Performance ID {sales_performance.id} updated by User ID {current_user['id']}.")
        return sales_performance.serialize(), 200

    @sales_performance_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Sales Performance not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, performance_id):
        """Soft delete a sales performance record (admin only)."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'admin'):
            logger.warning(f"Unauthorized delete attempt by User ID {current_user['id']} on Sales Performance ID {performance_id}.")
            return {'message': 'Unauthorized'}, 403

        sales_performance = SalesPerformance.query.filter_by(id=performance_id, is_deleted=False).first()
        if not sales_performance:
            logger.error(f"Sales Performance ID {performance_id} not found for deletion.")
            return {'message': 'Sales Performance not found'}, 404

        sales_performance.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='sales_performance',
            resource_id=sales_performance.id,
            details=f"User soft-deleted Sales Performance with ID {sales_performance.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales Performance ID {sales_performance.id} soft-deleted by User ID {current_user['id']}.")
        return {'message': 'Sales Performance deleted successfully'}, 200