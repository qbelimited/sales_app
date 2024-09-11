from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.sales_model import Sale
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_
from datetime import datetime

# Define a namespace for the sales operations
sales_ns = Namespace('sales', description='Sales operations')

# Define models for Swagger documentation
sale_model = sales_ns.model('Sale', {
    'sale_manager_id': fields.Integer(required=True, description='Sale Manager ID'),
    'sales_executive_id': fields.Integer(required=True, description='Sales Executive ID'),
    'client_name': fields.String(required=True, description='Client Name'),
    'client_id_no': fields.String(required=False, description='Client ID Number'),
    'client_phone': fields.String(required=True, description='Client Phone Number'),
    'serial_number': fields.String(required=True, description='Serial Number'),
    'collection_platform': fields.String(required=False, description='Collection Platform'),
    'source_type': fields.String(required=False, description='Source Type'),
    'momo_reference_number': fields.String(required=False, description='Momo Reference Number'),
    'momo_transaction_id': fields.String(required=False, description='Momo Transaction ID'),
    'first_pay_with_momo': fields.Boolean(required=False, description='First Pay with Momo'),
    'subsequent_pay_source_type': fields.String(required=False, description='Subsequent Payment Source Type'),
    'bank_id': fields.Integer(required=False, description='Bank ID'),
    'bank_branch_id': fields.Integer(required=False, description='Bank Branch ID'),
    'bank_acc_number': fields.String(required=False, description='Bank Account Number'),
    'paypoint_name': fields.String(required=False, description='Paypoint Name'),
    'paypoint_branch': fields.String(required=False, description='Paypoint Branch'),
    'staff_id': fields.String(required=False, description='Staff ID'),
    'policy_type_id': fields.Integer(required=True, description='Policy Type ID'),
    'amount': fields.Float(required=True, description='Sale Amount'),
    'customer_called': fields.Boolean(required=False, description='Customer Called'),
    'geolocation_latitude': fields.Float(required=False, description='Geolocation Latitude'),
    'geolocation_longitude': fields.Float(required=False, description='Geolocation Longitude')
})

@sales_ns.route('/')
class SaleListResource(Resource):
    @sales_ns.doc(security='Bearer Auth')
    @jwt_required()
    @sales_ns.marshal_with(sale_model)
    def get(self):
        """Retrieve a list of sales with extended filters."""
        current_user = get_jwt_identity()

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

        sales_query = Sale.query.filter_by(is_deleted=False)

        if filter_by:
            sales_query = sales_query.filter(or_(
                Sale.client_name.ilike(f'%{filter_by}%'),
                Sale.client_phone.ilike(f'%{filter_by}%')
            ))

        if start_date and end_date:
            sales_query = sales_query.filter(and_(
                Sale.created_at >= datetime.strptime(start_date, '%Y-%m-%d'),
                Sale.created_at <= datetime.strptime(end_date, '%Y-%m-%d')
            ))

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
        sales = sales_query.order_by(sort_by).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        logger.info(f"User {current_user['id']} accessed sales list.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_list',
            resource_id=None,
            details=f"User accessed list of sales"
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
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400

        new_sale = Sale(
            user_id=current_user['id'],
            sale_manager_id=data.get('sale_manager_id'),
            sales_executive_id=data.get('sales_executive_id'),
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
            bank_id=data.get('bank_id'),
            bank_branch_id=data.get('bank_branch_id'),
            bank_acc_number=data.get('bank_acc_number'),
            paypoint_name=data.get('paypoint_name'),
            paypoint_branch=data.get('paypoint_branch'),
            staff_id=data.get('staff_id'),
            policy_type_id=data.get('policy_type_id'),
            amount=data.get('amount'),
            customer_called=data.get('customer_called'),
            geolocation_latitude=data.get('geolocation_latitude'),
            geolocation_longitude=data.get('geolocation_longitude')
        )

        # Check for duplicates and handle accordingly
        new_sale.check_duplicate()

        db.session.add(new_sale)
        db.session.commit()

        # Log the creation to audit trail
        logger.info(f"User {current_user['id']} created a new sale with ID {new_sale.id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sale',
            resource_id=new_sale.id,
            details=f"User created a new sale with ID {new_sale.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_sale.serialize(), 201


@sales_ns.route('/<int:sale_id>')
class SaleDetailResource(Resource):
    @sales_ns.doc(security='Bearer Auth', responses={200: 'OK', 404: 'Sale Not Found'})
    @jwt_required()
    @sales_ns.marshal_with(sale_model)
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
        sale.paypoint_name = data.get('paypoint_name', sale.paypoint_name)
        sale.paypoint_branch = data.get('paypoint_branch', sale.paypoint_branch)
        sale.staff_id = data.get('staff_id', sale.staff_id)
        sale.policy_type_id = data.get('policy_type_id', sale.policy_type_id)
        sale.amount = data.get('amount', sale.amount)
        sale.customer_called = data.get('customer_called', sale.customer_called)
        sale.geolocation_latitude = data.get('geolocation_latitude', sale.geolocation_latitude)
        sale.geolocation_longitude = data.get('geolocation_longitude', sale.geolocation_longitude)
        sale.updated_at = datetime.utcnow()
        sale.status = 'updated'

        db.session.commit()

        # Log the update to audit trail
        logger.info(f"User {current_user['id']} updated sale with ID {sale.id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sale',
            resource_id=sale.id,
            details=f"User updated sale with ID {sale.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return sale.serialize(), 200

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
            details=f"User soft-deleted sale with ID {sale.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Sale deleted successfully'}, 200
