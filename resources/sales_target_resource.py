from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import User
from models.performance_model import SalesTarget, SalesPerformance
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip
from functools import lru_cache
from sqlalchemy import and_, or_

# Define a namespace for Sales Target operations
sales_target_ns = Namespace('sales_target', description='Sales Target operations')

# Define model for Swagger documentation
sales_target_model = sales_target_ns.model('SalesTarget', {
    'id': fields.Integer(description='Sales Target ID'),
    'sales_manager_id': fields.Integer(required=True, description='Sales Manager ID'),
    'target_sales_count': fields.Integer(required=True, description='Target number of sales'),
    'target_premium_amount': fields.Float(required=True, description='Target premium amount'),
    'target_criteria_type': fields.String(required=False, description='Target criteria type (e.g., source_type, product_group)'),
    'target_criteria_value': fields.String(required=False, description='Target criteria value (e.g., paypoint, risk)'),
    'period_start': fields.DateTime(required=False, description='Start date of the target period'),
    'period_end': fields.DateTime(required=False, description='End date of the target period'),
    'created_at': fields.DateTime(description='Creation date of the Sales Target'),
    'is_active': fields.Boolean(description='Is the target currently active')
})


@lru_cache(maxsize=100)
def validate_target_period_overlap(sales_manager_id, start_date, end_date, exclude_target_id=None):
    """Validate if the target period overlaps with existing targets."""
    query = SalesTarget.query.filter(
        SalesTarget.sales_manager_id == sales_manager_id,
        SalesTarget.is_deleted == False,
        or_(
            and_(
                SalesTarget.period_start <= start_date,
                SalesTarget.period_end >= start_date
            ),
            and_(
                SalesTarget.period_start <= end_date,
                SalesTarget.period_end >= end_date
            ),
            and_(
                SalesTarget.period_start >= start_date,
                SalesTarget.period_end <= end_date
            )
        )
    )

    if exclude_target_id:
        query = query.filter(SalesTarget.id != exclude_target_id)

    return not query.first()


def validate_target_period(start_date, end_date):
    """Validate target period dates."""
    if not start_date or not end_date:
        return True
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        return start_date < end_date
    except ValueError:
        return False


def validate_target_amounts(sales_count, premium_amount):
    """Validate target amounts."""
    return (
        isinstance(sales_count, int) and
        isinstance(premium_amount, (int, float)) and
        sales_count > 0 and
        premium_amount > 0
    )


def validate_criteria_type(criteria_type):
    """Validate criteria type."""
    valid_types = ['source_type', 'product_group', 'overall', 'custom']
    return criteria_type in valid_types if criteria_type else True


def validate_criteria_value(criteria_value, criteria_type):
    """Validate criteria value based on type."""
    if not criteria_value or not criteria_type:
        return True
    if criteria_type == 'source_type':
        valid_values = ['paypoint', 'bank', 'momo', 'other']
        return criteria_value in valid_values
    elif criteria_type == 'product_group':
        valid_values = ['risk', 'savings', 'investment']
        return criteria_value in valid_values
    return True


def validate_target_data(data, exclude_target_id=None):
    """Validate all target data before creation or update."""
    # Validate required fields
    required_fields = ['sales_manager_id', 'target_sales_count', 'target_premium_amount']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f'Missing required fields: {", ".join(missing_fields)}')

    # Validate target amounts
    if not validate_target_amounts(data['target_sales_count'], data['target_premium_amount']):
        raise ValueError('Invalid target amounts. Both must be positive numbers.')

    # Validate period dates
    if 'period_start' in data and 'period_end' in data:
        if not validate_target_period(data['period_start'], data['period_end']):
            raise ValueError('Invalid period dates. End date must be after start date.')

        # Check for period overlap
        if not validate_target_period_overlap(
            data['sales_manager_id'],
            data['period_start'],
            data['period_end'],
            exclude_target_id
        ):
            raise ValueError('Target period overlaps with existing target.')

    # Validate criteria
    if 'target_criteria_type' in data:
        if not validate_criteria_type(data['target_criteria_type']):
            raise ValueError('Invalid target criteria type.')

        if 'target_criteria_value' in data:
            if not validate_criteria_value(data['target_criteria_value'], data['target_criteria_type']):
                raise ValueError('Invalid target criteria value for the given type.')


# Helper function to check role permissions
def check_role_permission(current_user, required_roles):
    return current_user['role'].lower() in required_roles


@sales_target_ns.route('/')
class SalesTargetListResource(Resource):
    @sales_target_ns.doc(security='Bearer Auth')
    @jwt_required()
    @sales_target_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @sales_target_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @sales_target_ns.param('filter_by', 'Filter by sales manager name', type='string')
    @sales_target_ns.param('sort_by', 'Sort by field (e.g., created_at)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of Sales Targets."""
        current_user = get_jwt_identity()

        # Pagination and filtering params
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        query = SalesTarget.query.filter_by(is_deleted=False)

        if filter_by:
            query = query.join(User).filter(User.name.ilike(f'%{filter_by}%'))

        sales_targets = query.order_by(getattr(SalesTarget, sort_by).desc()).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_target_list',
            details="User accessed list of Sales Targets",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
        if not check_role_permission(current_user, ['admin', 'manager']):
            logger.warning(f"Unauthorized attempt to create sales target by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate input data
        validate_target_data(data)

        # Parse datetime strings to datetime objects
        period_start = datetime.fromisoformat(data['period_start'].replace("Z", "+00:00"))
        period_end = datetime.fromisoformat(data['period_end'].replace("Z", "+00:00"))

        if not validate_target_period(period_start, period_end):
            return {'message': 'Period end must be after period start'}, 400

        # Validate Sales Manager
        sales_manager = User.query.filter_by(id=data['sales_manager_id']).first()
        if not sales_manager:
            logger.error(f"Sales Manager not found by user {current_user['id']}")
            return {'message': 'Sales Manager not found'}, 404

        try:
            new_target = SalesTarget(
                sales_manager_id=data['sales_manager_id'],
                target_sales_count=data['target_sales_count'],
                target_premium_amount=data['target_premium_amount'],
                target_criteria_type=data.get('target_criteria_type'),
                target_criteria_value=data.get('target_criteria_value'),
                period_start=period_start,
                period_end=period_end
            )
            db.session.add(new_target)
            db.session.commit()

            # Create initial performance record
            performance = SalesPerformance(
                sales_manager_id=data['sales_manager_id'],
                actual_sales_count=0,
                actual_premium_amount=0,
                target_id=new_target.id,
                criteria_type=data.get('target_criteria_type'),
                criteria_value=data.get('target_criteria_value'),
                performance_date=datetime.utcnow()
            )
            db.session.add(performance)
            db.session.commit()

            # Log the creation to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='sales_target',
                resource_id=new_target.id,
                details=f"Created new Sales Target for Sales Manager ID {new_target.sales_manager_id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Sales target created for Sales Manager ID {new_target.sales_manager_id} by user {current_user['id']}")

            return new_target.serialize(), 201
        except Exception as e:
            logger.error(f"Error creating sales target: {str(e)}")
            db.session.rollback()
            return {'message': 'Error creating sales target'}, 400


@sales_target_ns.route('/<int:target_id>')
class SalesTargetResource(Resource):
    @sales_target_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Sales Target not found', 403: 'Unauthorized'})
    @jwt_required()
    def get(self, target_id):
        """Retrieve a specific Sales Target by ID."""
        current_user = get_jwt_identity()

        target = SalesTarget.query.filter_by(id=target_id, is_deleted=False).first()
        if not target:
            logger.error(f"Sales target ID {target_id} not found by user {current_user['id']}")
            return {'message': 'Sales Target not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_target',
            resource_id=target_id,
            details=f"User accessed Sales Target with ID {target_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
        if not check_role_permission(current_user, ['admin', 'manager']):
            logger.warning(f"Unauthorized attempt to update sales target ID {target_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        target = SalesTarget.query.filter_by(id=target_id, is_deleted=False).first()
        if not target:
            logger.error(f"Sales target ID {target_id} not found for update by user {current_user['id']}")
            return {'message': 'Sales Target not found'}, 404

        data = request.json

        # Validate input data
        validate_target_data(data, exclude_target_id=target_id)

        try:
            # Parse datetime strings to datetime objects
            period_start = datetime.fromisoformat(data['period_start'].replace("Z", "+00:00"))
            period_end = datetime.fromisoformat(data['period_end'].replace("Z", "+00:00"))

            if not validate_target_period(period_start, period_end):
                return {'message': 'Period end must be after period start'}, 400

            target.sales_manager_id = data.get('sales_manager_id', target.sales_manager_id)
            target.target_sales_count = data.get('target_sales_count', target.target_sales_count)
            target.target_premium_amount = data.get('target_premium_amount', target.target_premium_amount)
            target.target_criteria_type = data.get('target_criteria_type', target.target_criteria_type)
            target.target_criteria_value = data.get('target_criteria_value', target.target_criteria_value)
            target.period_start = period_start
            target.period_end = period_end
            target.updated_at = datetime.utcnow()

            # Update related performance record
            performance = SalesPerformance.query.filter_by(target_id=target_id).first()
            if performance:
                performance.criteria_type = target.target_criteria_type
                performance.criteria_value = target.target_criteria_value
                performance.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the update to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='sales_target',
                resource_id=target.id,
                details=f"Updated Sales Target with ID {target.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Sales target ID {target_id} updated by user {current_user['id']}")

            return target.serialize(), 200
        except Exception as e:
            logger.error(f"Error updating sales target: {str(e)}")
            db.session.rollback()
            return {'message': 'Error updating sales target'}, 400

    @sales_target_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Sales Target not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, target_id):
        """Soft-delete a Sales Target (admin only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, ['admin']):
            logger.warning(f"Unauthorized attempt to delete sales target ID {target_id} by user {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        target = SalesTarget.query.filter_by(id=target_id, is_deleted=False).first()
        if not target:
            logger.error(f"Sales target ID {target_id} not found for deletion by user {current_user['id']}")
            return {'message': 'Sales Target not found'}, 404

        try:
            target.is_deleted = True
            target.updated_at = datetime.utcnow()

            # Soft delete related performance records
            performances = SalesPerformance.query.filter_by(target_id=target_id).all()
            for performance in performances:
                performance.is_deleted = True
                performance.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the deletion to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='DELETE',
                resource_type='sales_target',
                resource_id=target.id,
                details=f"Deleted Sales Target with ID {target.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Sales target ID {target_id} deleted by user {current_user['id']}")

            return {'message': 'Sales Target deleted successfully'}, 200
        except Exception as e:
            logger.error(f"Error deleting sales target: {str(e)}")
            db.session.rollback()
            return {'message': 'Error deleting sales target'}, 400
