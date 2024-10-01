from flask_restx import Namespace, Resource, fields
from flask import request
from models.sales_model import Sale
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_
from datetime import datetime
from utils import get_client_ip

# Define a namespace for sales operations
sales_ns = Namespace('sales', description='Sales operations')

# Define model for Swagger documentation
sale_model = sales_ns.model('Sale', {
    'sale_manager_id': fields.Integer(required=True, description='Sale Manager ID'),
    'sales_executive_id': fields.Integer(required=True, description='Sales Executive ID'),
    'client_name': fields.String(required=True, description='Client Name'),
    'client_id_no': fields.String(description='Client ID Number'),
    'client_phone': fields.String(required=True, description='Client Phone Number'),
    'serial_number': fields.String(required=True, description='Serial Number'),
    'collection_platform': fields.String(description='Collection Platform'),
    'source_type': fields.String(description='Source Type'),
    'momo_reference_number': fields.String(description='Momo Reference Number'),
    'momo_transaction_id': fields.String(description='Momo Transaction ID'),
    'first_pay_with_momo': fields.Boolean(description='First Pay with Momo'),
    'subsequent_pay_source_type': fields.String(description='Subsequent Payment Source Type'),
    'bank_id': fields.Integer(description='Bank ID', allow_none=True),
    'bank_branch_id': fields.Integer(description='Bank Branch ID', allow_none=True),
    'bank_acc_number': fields.String(description='Bank Account Number'),
    'paypoint_id': fields.Integer(description='Paypoint ID', allow_none=True),
    'paypoint_branch': fields.String(description='Paypoint Branch'),
    'staff_id': fields.String(description='Staff ID'),
    'policy_type_id': fields.Integer(required=True, description='Policy Type ID'),
    'amount': fields.Float(required=True, description='Sale Amount'),
    'customer_called': fields.Boolean(description='Customer Called'),
    'geolocation_latitude': fields.Float(description='Geolocation Latitude'),
    'geolocation_longitude': fields.Float(description='Geolocation Longitude')
})

@sales_ns.route('/')
class SaleListResource(Resource):
    @sales_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Retrieve a list of sales with extended filters."""
        current_user = get_jwt_identity()

        # Pagination and filtering
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        # Extended filters
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        sales_executive_id = request.args.get('sales_executive_id', None, type=int)
        branch_id = request.args.get('branch_id', None, type=int)
        min_amount = request.args.get('min_amount', None, type=float)
        max_amount = request.args.get('max_amount', None, type=float)
        status = request.args.get('status', None)

        # Base query
        sales_query = Sale.query.filter_by(is_deleted=False)

        if filter_by:
            sales_query = sales_query.filter(or_(
                Sale.client_name.ilike(f'%{filter_by}%'),
                Sale.client_phone.ilike(f'%{filter_by}%')
            ))

        # Date range filter
        if start_date and end_date:
            try:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d')
                sales_query = sales_query.filter(and_(
                    Sale.created_at >= start_date_parsed,
                    Sale.created_at <= end_date_parsed
                ))
            except ValueError:
                return {'message': 'Invalid date format. Use YYYY-MM-DD.'}, 400

        if sales_executive_id:
            sales_query = sales_query.filter(Sale.sales_executive_id == sales_executive_id)

        if branch_id:
            sales_query = sales_query.filter(Sale.bank_branch_id == branch_id)

        if min_amount:
            sales_query = sales_query.filter(Sale.amount >= min_amount)

        if max_amount:
            sales_query = sales_query.filter(Sale.amount <= max_amount)

        if status:
            sales_query = sales_query.filter(Sale.status == status)

        # Apply sorting and pagination
        try:
            sales = sales_query.order_by(sort_by).paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            logger.error(f"Error retrieving sales list: {str(e)}")
            return {'message': 'Error retrieving sales list.'}, 500

        # Log the access to audit trail
        logger.info(f"User {current_user['id']} accessed sales list.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_list',
            resource_id=None,
            details="User accessed the list of sales.",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'sales': [sale.serialize() for sale in sales.items],
            'total': sales.total,
            'pages': sales.pages,
            'current_page': sales.page
        }, 200

    @sales_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Invalid Input'})
    @jwt_required()
    @sales_ns.expect(sale_model, validate=True)
    def post(self):
        """Create a new sale."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate required fields
        required_fields = ['sales_executive_id', 'client_phone', 'amount', 'sale_manager_id', 'policy_type_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                return {'message': f'Missing required field: {field}'}, 400

        try:
            # Extract optional fields with defaults
            bank_id = data.get('bank_id')
            bank_branch_id = data.get('bank_branch_id')
            paypoint_id = data.get('paypoint_id')
            geolocation_latitude = data.get('geolocation_latitude')
            geolocation_longitude = data.get('geolocation_longitude')

            # Create new sale
            new_sale = Sale(
                user_id=current_user['id'],
                sale_manager_id=data['sale_manager_id'],
                sales_executive_id=data['sales_executive_id'],
                client_name=data.get('client_name'),
                client_id_no=data.get('client_id_no'),
                client_phone=data.get('client_phone'),
                serial_number=data.get('serial_number'),
                collection_platform=data.get('collection_platform'),
                source_type=data.get('source_type'),
                momo_reference_number=data.get('momo_reference_number'),
                momo_transaction_id=data.get('momo_transaction_id'),
                first_pay_with_momo=data.get('first_pay_with_momo'),
                subsequent_pay_source_type=data.get('subsequent_pay_source_type'),
                bank_id=bank_id,
                bank_branch_id=bank_branch_id,
                bank_acc_number=data.get('bank_acc_number'),
                paypoint_id=paypoint_id,
                paypoint_branch=data.get('paypoint_branch'),
                staff_id=data.get('staff_id'),
                policy_type_id=data['policy_type_id'],
                amount=data['amount'],
                customer_called=data.get('customer_called'),
                geolocation_latitude=geolocation_latitude,
                geolocation_longitude=geolocation_longitude
            )

            # Check for duplicates and flag them if found
            new_sale = new_sale.check_duplicate()

            db.session.add(new_sale)
            db.session.commit()

            # Log the creation to audit trail
            logger.info(f"User {current_user['id']} created a new sale with ID {new_sale.id}.")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='sale',
                resource_id=new_sale.id,
                details=f"User created a new sale with ID {new_sale.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return new_sale.serialize(), 201
        except Exception as e:
            logger.error(f"Error creating sale: {str(e)}")
            return {'message': 'Error creating sale. Please check your input and try again.'}, 400

@sales_ns.route('/check-serial')
class SerialNumberCheckResource(Resource):
    @sales_ns.doc(security='Bearer Auth', responses={200: 'OK', 400: 'Invalid Input'})
    @jwt_required()
    def get(self):
        """Check if a serial number exists."""
        serial_number = request.args.get('serial_number')
        if not serial_number:
            return {'message': 'Serial number not provided'}, 400

        exists = Sale.query.filter_by(serial_number=serial_number, is_deleted=False).first() is not None

        return {'exists': exists}, 200

@sales_ns.route('/<int:sale_id>')
class SaleDetailResource(Resource):
    @sales_ns.doc(security='Bearer Auth', responses={200: 'OK', 404: 'Sale Not Found'})
    @jwt_required()
    def get(self, sale_id):
        """Retrieve a single sale by ID."""
        current_user = get_jwt_identity()

        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return {'message': 'Sale not found'}, 404

        # Log the access to audit trail
        logger.info(f"User {current_user['id']} accessed a sale with ID {sale_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sale',
            resource_id=sale_id,
            details=f"User accessed sale with ID {sale_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return sale.serialize(), 200

    @sales_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Sale Not Found'})
    @jwt_required()
    @sales_ns.expect(sale_model, validate=True)
    def put(self, sale_id):
        """Update an existing sale by ID."""
        current_user = get_jwt_identity()
        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return {'message': 'Sale not found'}, 404

        data = request.json

        try:
            # Update fields
            sale.sale_manager_id = data.get('sale_manager_id', sale.sale_manager_id)
            sale.sales_executive_id = data.get('sales_executive_id', sale.sales_executive_id)
            sale.client_name = data.get('client_name', sale.client_name)
            sale.client_id_no = data.get('client_id_no', sale.client_id_no)
            sale.client_phone = data.get('client_phone', sale.client_phone)
            sale.serial_number = data.get('serial_number', sale.serial_number)
            sale.collection_platform = data.get('collection_platform', sale.collection_platform)
            sale.source_type = data.get('source_type', sale.source_type)
            sale.momo_reference_number = data.get('momo_reference_number', sale.momo_reference_number)
            sale.momo_transaction_id = data.get('momo_transaction_id', sale.momo_transaction_id)
            sale.first_pay_with_momo = data.get('first_pay_with_momo', sale.first_pay_with_momo)
            sale.subsequent_pay_source_type = data.get('subsequent_pay_source_type', sale.subsequent_pay_source_type)
            sale.bank_id = data.get('bank_id', sale.bank_id)
            sale.bank_branch_id = data.get('bank_branch_id', sale.bank_branch_id)
            sale.bank_acc_number = data.get('bank_acc_number', sale.bank_acc_number)
            sale.paypoint_id = data.get('paypoint_id', sale.paypoint_id)
            sale.paypoint_branch = data.get('paypoint_branch', sale.paypoint_branch)
            sale.staff_id = data.get('staff_id', sale.staff_id)
            sale.policy_type_id = data.get('policy_type_id', sale.policy_type_id)
            sale.amount = data.get('amount', sale.amount)
            sale.customer_called = data.get('customer_called', sale.customer_called)
            sale.geolocation_latitude = data.get('geolocation_latitude', sale.geolocation_latitude)
            sale.geolocation_longitude = data.get('geolocation_longitude', sale.geolocation_longitude)
            sale.updated_at = datetime.utcnow()
            sale.status = 'updated'

            # Check for duplicates during update
            sale = sale.check_duplicate()
            db.session.commit()

            # Log the update to audit trail
            logger.info(f"User {current_user['id']} updated sale with ID {sale.id}.")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='sale',
                resource_id=sale.id,
                details=f"User updated sale with ID {sale.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return sale.serialize(), 200
        except Exception as e:
            logger.error(f"Error updating sale: {str(e)}")
            return {'message': 'Error updating sale. Please check your input and try again.'}, 400

    @sales_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Sale Not Found'})
    @jwt_required()
    def delete(self, sale_id):
        """Soft delete a sale by marking it as deleted."""
        current_user = get_jwt_identity()
        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return {'message': 'Sale not found'}, 404

        sale.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        logger.info(f"User {current_user['id']} soft-deleted sale with ID {sale.id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='sale',
            resource_id=sale.id,
            details=f"User soft-deleted sale with ID {sale.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Sale deleted successfully'}, 200
