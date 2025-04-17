from flask_restx import Namespace, Resource, fields
from flask import request
from models.sales_executive_model import SalesExecutive, ExecutiveStatus
from models.branch_model import Branch
from models.audit_model import AuditTrail
from models.performance_model import SalesPerformance
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip

# Define a namespace for Sales Executive operations
sales_executive_ns = Namespace(
    'sales_executive',
    description='Sales Executive operations'
)

# Define models for Swagger documentation
sales_executive_model = sales_executive_ns.model('SalesExecutive', {
    'id': fields.Integer(description='Sales Executive ID'),
    'name': fields.String(required=True, description='Sales Executive Name'),
    'code': fields.String(required=True, description='Sales Executive Code'),
    'manager_id': fields.Integer(required=True, description='Manager ID'),
    'branch_ids': fields.List(fields.Integer, description='List of Branch IDs'),
    'phone_number': fields.String(
        required=True,
        description='Sales Executive Phone Number'
    ),
    'email': fields.String(description='Sales Executive Email'),
    'status': fields.String(
        description='Sales Executive Status',
        enum=[status.value for status in ExecutiveStatus]
    ),
    'target_sales_count': fields.Integer(description='Target Sales Count'),
    'target_premium_amount': fields.Float(description='Target Premium Amount')
})

performance_model = sales_executive_ns.model('Performance', {
    'sales_executive_id': fields.Integer(description='Sales Executive ID'),
    'actual_sales_count': fields.Integer(description='Actual Sales Count'),
    'actual_premium_amount': fields.Float(description='Actual Premium Amount'),
    'target_sales_count': fields.Integer(description='Target Sales Count'),
    'target_premium_amount': fields.Float(description='Target Premium Amount'),
    'performance_date': fields.DateTime(description='Performance Date')
})

@sales_executive_ns.route('/')
class SalesExecutiveListResource(Resource):
    @sales_executive_ns.doc(security='Bearer Auth')
    @jwt_required()
    @sales_executive_ns.param(
        'page',
        'Page number for pagination',
        type='integer',
        default=1
    )
    @sales_executive_ns.param(
        'per_page',
        'Number of items per page',
        type='integer',
        default=10
    )
    @sales_executive_ns.param(
        'filter_by',
        'Filter by Sales Executive name',
        type='string'
    )
    @sales_executive_ns.param('status', 'Filter by status', type='string')
    @sales_executive_ns.param(
        'sort_by',
        'Sort by field (e.g., created_at, name)',
        type='string',
        default='created_at'
    )
    def get(self):
        """Retrieve a paginated list of Sales Executives."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        status = request.args.get('status', None)
        sort_by = request.args.get('sort_by', 'created_at')

        sales_executive_query = SalesExecutive.query.filter_by(is_deleted=False)

        if filter_by:
            sales_executive_query = sales_executive_query.filter(
                SalesExecutive.name.ilike(f'%{filter_by}%')
            )

        if status:
            sales_executive_query = sales_executive_query.filter_by(status=status)

        sales_executives = sales_executive_query.order_by(sort_by).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # Log the access to audit trail and logger
        logger.info(
            f"User {current_user['id']} accessed the list of Sales Executives."
        )
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_executive_list',
            resource_id=None,
            details="User accessed list of Sales Executives",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'sales_executives': [se.serialize() for se in sales_executives.items],
            'total': sales_executives.total,
            'pages': sales_executives.pages,
            'current_page': sales_executives.page
        }, 200

    @sales_executive_ns.doc(
        security='Bearer Auth',
        responses={
            201: 'Created',
            400: 'Bad Request',
            403: 'Unauthorized'
        }
    )
    @jwt_required()
    @sales_executive_ns.expect(sales_executive_model, validate=True)
    def post(self):
        """Create a new Sales Executive (admin and manager only)."""
        current_user = get_jwt_identity()

        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(
                f"Unauthorized attempt by User {current_user['id']} "
                "to create a new Sales Executive."
            )
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validation
        required_fields = [
            'name',
            'code',
            'manager_id',
            'branch_ids',
            'phone_number'
        ]
        if not all([data.get(field) for field in required_fields]):
            logger.error(
                f"User {current_user['id']} attempted to create a "
                "Sales Executive with missing fields."
            )
            return {'message': 'Missing required fields'}, 400

        # Validate email if provided
        if 'email' in data and data['email'] and '@' not in data['email']:
            return {'message': 'Invalid email format'}, 400

        # Validate status if provided
        if 'status' in data and data['status']:
            try:
                ExecutiveStatus(data['status'])
            except ValueError:
                return {'message': 'Invalid status'}, 400

        new_sales_executive = SalesExecutive(
            name=data['name'],
            code=data['code'],
            manager_id=data['manager_id'],
            phone_number=data['phone_number'],
            email=data.get('email'),
            status=data.get('status', ExecutiveStatus.ACTIVE.value),
            target_sales_count=data.get('target_sales_count'),
            target_premium_amount=data.get('target_premium_amount')
        )

        # Add branches to the sales executive
        branch_ids = data['branch_ids']
        for branch_id in branch_ids:
            branch = Branch.query.filter_by(id=branch_id).first()
            if branch:
                new_sales_executive.branches.append(branch)

        db.session.add(new_sales_executive)
        db.session.commit()

        # Log the creation to audit trail and logger
        logger.info(
            f"User {current_user['id']} created a new Sales Executive "
            f"with ID {new_sales_executive.id}."
        )
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sales_executive',
            resource_id=new_sales_executive.id,
            details=f"User created a new Sales Executive with ID {new_sales_executive.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return new_sales_executive.serialize(), 201

@sales_executive_ns.route('/<int:sales_executive_id>')
class SalesExecutiveResource(Resource):
    @sales_executive_ns.doc(
        security='Bearer Auth',
        responses={
            200: 'Success',
            404: 'Sales Executive not found',
            403: 'Unauthorized'
        }
    )
    @jwt_required()
    def get(self, sales_executive_id):
        """Retrieve a specific Sales Executive by ID."""
        current_user = get_jwt_identity()

        sales_executive = SalesExecutive.query.filter_by(
            id=sales_executive_id,
            is_deleted=False
        ).first()
        if not sales_executive:
            logger.error(
                f"Sales Executive with ID {sales_executive_id} not found "
                f"for User {current_user['id']}."
            )
            return {'message': 'Sales Executive not found'}, 404

        # Log the access to audit trail and logger
        logger.info(
            f"User {current_user['id']} accessed Sales Executive "
            f"with ID {sales_executive_id}."
        )
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_executive',
            resource_id=sales_executive_id,
            details=f"User accessed Sales Executive with ID {sales_executive_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return sales_executive.serialize(), 200

    @sales_executive_ns.doc(
        security='Bearer Auth',
        responses={
            200: 'Updated',
            404: 'Sales Executive not found',
            403: 'Unauthorized'
        }
    )
    @jwt_required()
    @sales_executive_ns.expect(sales_executive_model, validate=True)
    def put(self, sales_executive_id):
        """Update an existing Sales Executive (admin and manager only)."""
        current_user = get_jwt_identity()

        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(
                f"Unauthorized update attempt by User {current_user['id']} "
                f"on Sales Executive {sales_executive_id}."
            )
            return {'message': 'Unauthorized'}, 403

        sales_executive = SalesExecutive.query.filter_by(
            id=sales_executive_id,
            is_deleted=False
        ).first()
        if not sales_executive:
            logger.error(
                f"Sales Executive with ID {sales_executive_id} not found "
                f"for update by User {current_user['id']}."
            )
            return {'message': 'Sales Executive not found'}, 404

        data = request.json

        # Validate email if provided
        if 'email' in data and data['email'] and '@' not in data['email']:
            return {'message': 'Invalid email format'}, 400

        # Validate status if provided
        if 'status' in data and data['status']:
            try:
                ExecutiveStatus(data['status'])
            except ValueError:
                return {'message': 'Invalid status'}, 400

        # Update fields
        sales_executive.name = data.get('name', sales_executive.name)
        sales_executive.code = data.get('code', sales_executive.code)
        sales_executive.manager_id = data.get('manager_id', sales_executive.manager_id)
        sales_executive.phone_number = data.get('phone_number', sales_executive.phone_number)
        sales_executive.email = data.get('email', sales_executive.email)
        sales_executive.status = data.get('status', sales_executive.status)
        sales_executive.target_sales_count = data.get(
            'target_sales_count',
            sales_executive.target_sales_count
        )
        sales_executive.target_premium_amount = data.get(
            'target_premium_amount',
            sales_executive.target_premium_amount
        )

        # Update branches
        if 'branch_ids' in data:
            sales_executive.branches = []  # Clear existing branches
            branch_ids = data['branch_ids']
            for branch_id in branch_ids:
                branch = Branch.query.filter_by(id=branch_id).first()
                if branch:
                    sales_executive.branches.append(branch)

        sales_executive.updated_at = datetime.utcnow()
        db.session.commit()

        # Log the update to audit trail and logger
        logger.info(
            f"User {current_user['id']} updated Sales Executive {sales_executive_id}."
        )
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_executive',
            resource_id=sales_executive.id,
            details=f"User updated Sales Executive with ID {sales_executive.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return sales_executive.serialize(), 200

    @sales_executive_ns.doc(
        security='Bearer Auth',
        responses={
            200: 'Deleted',
            404: 'Sales Executive not found',
            403: 'Unauthorized'
        }
    )
    @jwt_required()
    def delete(self, sales_executive_id):
        """Soft-delete a Sales Executive (admin and manager only)."""
        current_user = get_jwt_identity()

        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(
                f"Unauthorized deletion attempt by User {current_user['id']} "
                f"on Sales Executive {sales_executive_id}."
            )
            return {'message': 'Unauthorized'}, 403

        sales_executive = SalesExecutive.query.filter_by(
            id=sales_executive_id,
            is_deleted=False
        ).first()
        if not sales_executive:
            logger.error(
                f"Sales Executive with ID {sales_executive_id} not found "
                f"for deletion by User {current_user['id']}."
            )
            return {'message': 'Sales Executive not found'}, 404

        sales_executive.is_deleted = True
        sales_executive.status = ExecutiveStatus.TERMINATED.value
        db.session.commit()

        # Log the deletion to audit trail and logger
        logger.info(
            f"User {current_user['id']} deleted Sales Executive {sales_executive_id}."
        )
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='sales_executive',
            resource_id=sales_executive.id,
            details=f"User soft-deleted Sales Executive with ID {sales_executive.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Sales Executive deleted successfully'}, 200

@sales_executive_ns.route('/<int:sales_executive_id>/performance')
class SalesExecutivePerformanceResource(Resource):
    @sales_executive_ns.doc(
        security='Bearer Auth',
        responses={200: 'Success', 404: 'Sales Executive not found'}
    )
    @jwt_required()
    @sales_executive_ns.param(
        'start_date',
        'Start date for performance period',
        type='string'
    )
    @sales_executive_ns.param(
        'end_date',
        'End date for performance period',
        type='string'
    )
    def get(self, sales_executive_id):
        """Get performance metrics for a specific Sales Executive."""
        current_user = get_jwt_identity()

        sales_executive = SalesExecutive.query.filter_by(
            id=sales_executive_id,
            is_deleted=False
        ).first()
        if not sales_executive:
            return {'message': 'Sales Executive not found'}, 404

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Query performance data
        performance_query = SalesPerformance.query.filter_by(
            sales_executive_id=sales_executive_id
        )

        if start_date:
            performance_query = performance_query.filter(
                SalesPerformance.performance_date >= start_date
            )
        if end_date:
            performance_query = performance_query.filter(
                SalesPerformance.performance_date <= end_date
            )

        performance_data = performance_query.all()

        # Calculate totals
        total_sales = sum(p.actual_sales_count for p in performance_data)
        total_premium = sum(p.actual_premium_amount for p in performance_data)
        target_sales = sales_executive.target_sales_count or 0
        target_premium = sales_executive.target_premium_amount or 0

        return {
            'sales_executive': sales_executive.serialize(),
            'performance': {
                'total_sales': total_sales,
                'total_premium': total_premium,
                'target_sales': target_sales,
                'target_premium': target_premium,
                'sales_achievement': (
                    (total_sales / target_sales * 100) if target_sales > 0 else 0
                ),
                'premium_achievement': (
                    (total_premium / target_premium * 100) if target_premium > 0 else 0
                ),
                'performance_data': [p.serialize() for p in performance_data]
            }
        }, 200
