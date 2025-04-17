from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive, ExecutiveStatus
from models.audit_model import AuditTrail
from models.performance_model import SalesPerformance, SalesTarget
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip
from sqlalchemy import func

# Define a namespace for manager-related operations
manager_ns = Namespace('manager', description='Manager operations')

# Define models for Swagger documentation
sales_executive_model = manager_ns.model('SalesExecutive', {
    'id': fields.Integer(description='Sales Executive ID'),
    'name': fields.String(required=True, description='Sales Executive Name'),
    'code': fields.String(required=True, description='Sales Executive Code'),
    'manager_id': fields.Integer(description='Manager ID'),
    'phone_number': fields.String(description='Sales Executive Phone Number'),
    'email': fields.String(description='Sales Executive Email'),
    'status': fields.String(description='Sales Executive Status', enum=[status.value for status in ExecutiveStatus]),
    'target_sales_count': fields.Integer(description='Target Sales Count'),
    'target_premium_amount': fields.Float(description='Target Premium Amount'),
    'branch_ids': fields.List(fields.Integer, description='List of Branch IDs')
})

performance_model = manager_ns.model('Performance', {
    'sales_executive_id': fields.Integer(description='Sales Executive ID'),
    'actual_sales_count': fields.Integer(description='Actual Sales Count'),
    'actual_premium_amount': fields.Float(description='Actual Premium Amount'),
    'target_sales_count': fields.Integer(description='Target Sales Count'),
    'target_premium_amount': fields.Float(description='Target Premium Amount'),
    'performance_date': fields.DateTime(description='Performance Date')
})

# Helper function to check role permissions
def check_role_permission(current_user):
    return current_user['role'].lower() in ['admin', 'manager']

@manager_ns.route('/sales_executives')
class ManagerSalesExecutiveResource(Resource):
    @manager_ns.doc(security='Bearer Auth')
    @jwt_required()
    @manager_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @manager_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @manager_ns.param('status', 'Filter by status', type='string')
    def get(self):
        """Retrieve all sales executives managed by the current manager, with pagination."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            logger.warning(f"Unauthorized access attempt by User ID {current_user.get('id')} to retrieve sales executives.")
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')

        # Get sales executives under this manager
        query = SalesExecutive.query.filter_by(manager_id=current_user['id'], is_deleted=False)
        if status:
            query = query.filter_by(status=status)
        sales_executives = query.paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_executive_list',
            details="Manager accessed list of sales executives",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'sales_executives': [se.serialize() for se in sales_executives.items],
            'total': sales_executives.total,
            'pages': sales_executives.pages,
            'current_page': sales_executives.page,
            'has_next': sales_executives.has_next,
            'has_prev': sales_executives.has_prev
        })

    @manager_ns.doc(security='Bearer Auth', responses={201: 'Created', 403: 'Unauthorized'})
    @jwt_required()
    @manager_ns.expect(sales_executive_model, validate=True)
    def post(self):
        """Create a new sales executive under the current manager."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            logger.warning(f"Unauthorized sales executive creation attempt by User ID {current_user.get('id')}.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validation for phone number (if provided)
        phone_number = data.get('phone_number')
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
            logger.error(f"Invalid phone number provided by User ID {current_user.get('id')}.")
            return {'message': 'Invalid phone number. Must be 10 digits.'}, 400

        # Validation for email (if provided)
        email = data.get('email')
        if email and '@' not in email:
            logger.error(f"Invalid email provided by User ID {current_user.get('id')}.")
            return {'message': 'Invalid email format.'}, 400

        new_sales_executive = SalesExecutive(
            name=data['name'],
            code=data['code'],
            manager_id=current_user['id'],
            phone_number=phone_number,
            email=email,
            status=data.get('status', ExecutiveStatus.ACTIVE.value),
            target_sales_count=data.get('target_sales_count'),
            target_premium_amount=data.get('target_premium_amount')
        )

        # Add branches if provided
        if 'branch_ids' in data:
            from models.branch_model import Branch
            for branch_id in data['branch_ids']:
                branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
                if branch:
                    new_sales_executive.branches.append(branch)

        db.session.add(new_sales_executive)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sales_executive',
            resource_id=new_sales_executive.id,
            details=f"Manager created a new sales executive with ID {new_sales_executive.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales executive created by Manager ID {current_user['id']} with Executive ID {new_sales_executive.id}.")
        return new_sales_executive.serialize(), 201

@manager_ns.route('/sales_executives/<int:executive_id>')
class ManagerSalesExecutiveUpdateResource(Resource):
    @manager_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Sales Executive not found', 403: 'Unauthorized'})
    @jwt_required()
    @manager_ns.expect(sales_executive_model, validate=True)
    def put(self, executive_id):
        """Update an existing sales executive's details."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            logger.warning(f"Unauthorized update attempt by User ID {current_user.get('id')} on Sales Executive ID {executive_id}.")
            return {'message': 'Unauthorized'}, 403

        sales_executive = SalesExecutive.query.filter_by(id=executive_id, is_deleted=False).first()
        if not sales_executive or sales_executive.manager_id != current_user['id']:
            logger.error(f"Sales Executive ID {executive_id} not found or unauthorized access by User ID {current_user.get('id')}.")
            return {'message': 'Sales Executive not found or unauthorized'}, 404

        data = request.json

        # Validation for phone number (if provided)
        phone_number = data.get('phone_number')
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
            logger.error(f"Invalid phone number update attempt by User ID {current_user.get('id')} for Sales Executive ID {executive_id}.")
            return {'message': 'Invalid phone number. Must be 10 digits.'}, 400

        # Validation for email (if provided)
        email = data.get('email')
        if email and '@' not in email:
            logger.error(f"Invalid email update attempt by User ID {current_user.get('id')} for Sales Executive ID {executive_id}.")
            return {'message': 'Invalid email format.'}, 400

        # Update fields
        sales_executive.name = data.get('name', sales_executive.name)
        sales_executive.code = data.get('code', sales_executive.code)
        sales_executive.phone_number = phone_number if phone_number else sales_executive.phone_number
        sales_executive.email = email if email else sales_executive.email
        sales_executive.status = data.get('status', sales_executive.status)
        sales_executive.target_sales_count = data.get('target_sales_count', sales_executive.target_sales_count)
        sales_executive.target_premium_amount = data.get('target_premium_amount', sales_executive.target_premium_amount)
        sales_executive.updated_at = datetime.utcnow()

        # Update branches if provided
        if 'branch_ids' in data:
            sales_executive.branches = []
            from models.branch_model import Branch
            for branch_id in data['branch_ids']:
                branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
                if branch:
                    sales_executive.branches.append(branch)

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_executive',
            resource_id=sales_executive.id,
            details=f"Manager updated sales executive with ID {sales_executive.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales Executive ID {sales_executive.id} updated by Manager ID {current_user['id']}.")
        return sales_executive.serialize(), 200

@manager_ns.route('/performance')
class ManagerPerformanceResource(Resource):
    @manager_ns.doc(security='Bearer Auth')
    @jwt_required()
    @manager_ns.param('start_date', 'Start date for performance period', type='string')
    @manager_ns.param('end_date', 'End date for performance period', type='string')
    def get(self):
        """Get performance metrics for all sales executives under the manager."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            logger.warning(f"Unauthorized performance access attempt by User ID {current_user.get('id')}.")
            return {'message': 'Unauthorized'}, 403

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get all sales executives under this manager
        sales_executives = SalesExecutive.query.filter_by(
            manager_id=current_user['id'],
            is_deleted=False
        ).all()

        performance_data = []
        for se in sales_executives:
            # Get performance metrics
            query = SalesPerformance.query.filter_by(sales_executive_id=se.id)
            if start_date:
                query = query.filter(SalesPerformance.performance_date >= start_date)
            if end_date:
                query = query.filter(SalesPerformance.performance_date <= end_date)

            performance = query.first()
            if performance:
                performance_data.append({
                    'sales_executive_id': se.id,
                    'sales_executive_name': se.name,
                    'actual_sales_count': performance.actual_sales_count,
                    'actual_premium_amount': performance.actual_premium_amount,
                    'target_sales_count': se.target_sales_count,
                    'target_premium_amount': se.target_premium_amount,
                    'performance_date': performance.performance_date
                })

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='performance',
            details="Manager accessed performance metrics",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({'performance': performance_data})
