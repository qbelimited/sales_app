from flask_restx import Namespace, Resource, fields
from flask import request
from models.performance_model import SalesPerformance, SalesTarget
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip

# Define a namespace for sales performance-related operations
sales_performance_ns = Namespace('sales_performance', description='Sales Performance operations')

# Define models for Swagger documentation
sales_performance_model = sales_performance_ns.model('SalesPerformance', {
    'id': fields.Integer(description='Sales Performance ID'),
    'sales_manager_id': fields.Integer(required=True, description='Sales Manager ID'),
    'actual_sales_count': fields.Integer(required=True, description='Actual number of sales made'),
    'actual_premium_amount': fields.Float(required=True, description='Actual premium amount sold'),
    'target_id': fields.Integer(description='Sales Target ID'),
    'criteria_type': fields.String(description='Criteria Type (e.g., source_type, product_group)'),
    'criteria_value': fields.String(description='Criteria Value (e.g., paypoint, risk)'),
    'criteria_met_count': fields.Integer(description='Count of sales that met the criteria'),
    'performance_date': fields.DateTime(description='Performance date'),
})

# Helper function to check role permissions
def check_role_permission(current_user, required_roles):
    """Helper function to validate the user's role."""
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'sales_manager': ['admin', 'manager', 'back_office', 'sales_manager']
    }
    return current_user['role'].lower() in roles.get(required_roles, [])

def get_actual_sales_count(target):
    # Example query to get actual sales count based on criteria in the target
    return SalesPerformance.query.filter(
        SalesPerformance.sales_manager_id == target.sales_manager_id,
        SalesPerformance.criteria_type == target.target_criteria_type,
        SalesPerformance.criteria_value == target.target_criteria_value,
        SalesPerformance.is_deleted == False
    ).count()

def get_actual_premium_amount(target):
    # Example query to calculate the actual premium amount based on criteria in the target
    return db.session.query(db.func.sum(SalesPerformance.actual_premium_amount)).filter(
        SalesPerformance.sales_manager_id == target.sales_manager_id,
        SalesPerformance.criteria_type == target.target_criteria_type,
        SalesPerformance.criteria_value == target.target_criteria_value,
        SalesPerformance.is_deleted == False
    ).scalar() or 0.0

def get_criteria_met_count(target):
    # Count of sales that met the criteria
    return SalesPerformance.query.filter(
        SalesPerformance.sales_manager_id == target.sales_manager_id,
        SalesPerformance.criteria_type == target.target_criteria_type,
        SalesPerformance.criteria_value == target.target_criteria_value,
        SalesPerformance.is_deleted == False
    ).count()

@sales_performance_ns.route('/')
class SalesPerformanceResource(Resource):
    @sales_performance_ns.doc(security='Bearer Auth')
    @jwt_required()
    @sales_performance_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @sales_performance_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @sales_performance_ns.param('sales_manager_id', 'Filter by Sales Manager ID', type='integer')
    @sales_performance_ns.param('target_id', 'Filter by Sales Target ID', type='integer')
    @sales_performance_ns.param('criteria_type', 'Filter by Criteria Type (e.g., source_type)', type='string')
    @sales_performance_ns.param('criteria_value', 'Filter by Criteria Value (e.g., paypoint)', type='string')
    def get(self):
        """Retrieve sales performance records with pagination and optional filters."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'sales_manager'):
            logger.warning(f"Unauthorized access attempt by User ID {current_user['id']} to retrieve sales performances.")
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sales_manager_id = request.args.get('sales_manager_id')
        target_id = request.args.get('target_id')
        criteria_type = request.args.get('criteria_type')
        criteria_value = request.args.get('criteria_value')

        # Build query based on filters
        query = SalesPerformance.query.filter_by(is_deleted=False)
        if sales_manager_id:
            query = query.filter_by(sales_manager_id=sales_manager_id)
        if target_id:
            query = query.filter_by(target_id=target_id)
        if criteria_type and criteria_value:
            query = query.filter_by(criteria_type=criteria_type, criteria_value=criteria_value)

        sales_performances = query.paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_performance_list',
            details="User accessed sales performance records",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'sales_performances': [sp.serialize() for sp in sales_performances.items],
            'total': sales_performances.total,
            'pages': sales_performances.pages,
            'current_page': sales_performances.page,
            'has_next': sales_performances.has_next,
            'has_prev': sales_performances.has_prev
        }

    @sales_performance_ns.doc(security='Bearer Auth', responses={201: 'Created', 403: 'Unauthorized'})
    @jwt_required()
    @sales_performance_ns.expect(sales_performance_model, validate=True)
    def post(self):
        """Create a new sales performance record (for managers or sales managers only)."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized sales performance creation attempt by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate the target ID exists
        target = SalesTarget.query.filter_by(id=data['target_id'], is_deleted=False).first()
        if not target:
            logger.error(f"Sales Target ID {data['target_id']} not found.")
            return {'message': 'Sales Target not found'}, 404

        # Calculate criteria met count
        criteria_met_count = get_criteria_met_count(target)

        # Create new sales performance with dynamic criteria
        new_sales_performance = SalesPerformance(
            sales_manager_id=data.get('sales_manager_id', current_user['id']),
            actual_sales_count=data['actual_sales_count'],
            actual_premium_amount=data['actual_premium_amount'],
            target_id=data['target_id'],
            criteria_type=data.get('criteria_type'),
            criteria_value=data.get('criteria_value'),
            criteria_met_count=criteria_met_count,
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
            details=f"User created sales performance with ID {new_sales_performance.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
            details=f"User accessed Sales Performance with ID {performance_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
        if not check_role_permission(current_user, 'manager'):
            logger.warning(f"Unauthorized update attempt by User ID {current_user['id']} on Sales Performance ID {performance_id}.")
            return {'message': 'Unauthorized'}, 403

        sales_performance = SalesPerformance.query.filter_by(id=performance_id, is_deleted=False).first()
        if not sales_performance:
            logger.error(f"Sales Performance ID {performance_id} not found for update.")
            return {'message': 'Sales Performance not found'}, 404

        data = request.json
        sales_performance.actual_sales_count = data.get('actual_sales_count', sales_performance.actual_sales_count)
        sales_performance.actual_premium_amount = data.get('actual_premium_amount', sales_performance.actual_premium_amount)
        sales_performance.criteria_type = data.get('criteria_type', sales_performance.criteria_type)
        sales_performance.criteria_value = data.get('criteria_value', sales_performance.criteria_value)

        # Recalculate criteria met count
        sales_performance.criteria_met_count = get_criteria_met_count(sales_performance)

        sales_performance.performance_date = data.get('performance_date', sales_performance.performance_date)
        sales_performance.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_performance',
            resource_id=sales_performance.id,
            details=f"User updated Sales Performance with ID {sales_performance.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
            details=f"User soft-deleted Sales Performance with ID {sales_performance.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales Performance ID {sales_performance.id} soft-deleted by User ID {current_user['id']}.")
        return {'message': 'Sales Performance deleted successfully'}, 200

@sales_performance_ns.route('/auto-generate')
class AutoGeneratePerformanceResource(Resource):
    @sales_performance_ns.doc(security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Automatically generate sales performance records for all sales managers based on targets."""
        try:
            # Fetch all active sales targets
            sales_targets = SalesTarget.query.filter_by(is_active=True, is_deleted=False).all()
            sales_performance_records = []

            for target in sales_targets:
                # Logic to calculate actual sales count and premium amount based on the target
                actual_sales_count = get_actual_sales_count(target)
                actual_premium_amount = get_actual_premium_amount(target)
                criteria_met_count = get_criteria_met_count(target)  # Calculate criteria met count

                # Create new sales performance record
                performance_record = SalesPerformance(
                    sales_manager_id=target.sales_manager_id,
                    actual_sales_count=actual_sales_count,
                    actual_premium_amount=actual_premium_amount,
                    target_id=target.id,
                    criteria_type=target.target_criteria_type,
                    criteria_value=target.target_criteria_value,
                    criteria_met_count=criteria_met_count,  # Include criteria met count
                    performance_date=datetime.utcnow().date()
                )
                db.session.add(performance_record)
                sales_performance_records.append(performance_record)

            db.session.commit()

            # Log the auto-generation to audit trail
            audit = AuditTrail(
                user_id=get_jwt_identity()['id'],
                action='ACCESS',
                resource_type='sales_performance',
                details=f"User auto-generated sales performance records for {len(sales_performance_records)} managers.",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': 'Sales performance records auto-generated successfully', 'records_count': len(sales_performance_records)}, 201

        except Exception as e:
            logger.error(f"Error during auto generation of sales performance: {e}")
            return {'message': 'Error during auto generation'}, 500


@sales_performance_ns.route('/auto-update')
class AutoUpdatePerformanceResource(Resource):
    @sales_performance_ns.doc(security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Automatically update sales performance records for all sales managers based on targets."""
        try:
            # Fetch all active sales targets
            sales_targets = SalesTarget.query.filter_by(is_active=True, is_deleted=False).all()
            updated_records_count = 0

            for target in sales_targets:
                # Logic to calculate actual sales count and premium amount based on the target
                actual_sales_count = get_actual_sales_count(target)
                actual_premium_amount = get_actual_premium_amount(target)

                # Check for existing performance record
                performance_record = SalesPerformance.query.filter_by(
                    sales_manager_id=target.sales_manager_id,
                    target_id=target.id,
                    criteria_type=target.target_criteria_type,
                    criteria_value=target.target_criteria_value,
                    performance_date=datetime.utcnow().date()  # Use today's date for the performance date
                ).first()

                if performance_record:
                    # Update existing record
                    performance_record.actual_sales_count = actual_sales_count
                    performance_record.actual_premium_amount = actual_premium_amount
                    performance_record.criteria_met_count = get_criteria_met_count(target)  # Update criteria met count
                    performance_record.updated_at = datetime.utcnow()
                    updated_records_count += 1

            db.session.commit()

            # Log the auto-update to audit trail
            audit = AuditTrail(
                user_id=get_jwt_identity()['id'],
                action='UPDATE',
                resource_type='sales_performance',
                details=f"User auto-updated sales performance records for {updated_records_count} managers.",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': 'Sales performance records auto-updated successfully', 'updated_count': updated_records_count}, 200

        except Exception as e:
            logger.error(f"Error during auto update of sales performance: {e}")
            return {'message': 'Error during auto update'}, 500
