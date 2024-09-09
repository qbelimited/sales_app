from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for manager-related operations
manager_ns = Namespace('manager', description='Manager operations')

# Define models for Swagger documentation
sales_executive_model = manager_ns.model('SalesExecutive', {
    'id': fields.Integer(description='Sales Executive ID'),
    'name': fields.String(required=True, description='Sales Executive Name'),
    'code': fields.String(required=True, description='Sales Executive Code'),
    'manager_id': fields.Integer(description='Manager ID'),
    'phone_number': fields.String(description='Sales Executive Phone Number'),
})

@manager_ns.route('/sales_executives')
class ManagerSalesExecutiveResource(Resource):
    @manager_ns.doc(security='Bearer Auth')
    @jwt_required()
    @manager_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @manager_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    def get(self):
        """Retrieve all sales executives managed by the current manager, with pagination."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            logger.warning(f"Unauthorized access attempt by User ID {current_user['id']} to retrieve sales executives.")
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Get sales executives under this manager
        sales_executives_query = SalesExecutive.query.filter_by(manager_id=current_user['id'], is_deleted=False)
        sales_executives = sales_executives_query.paginate(page, per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_executive_list',
            resource_id=None,
            details="Manager accessed list of sales executives"
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
        if current_user['role'] != 'manager':
            logger.warning(f"Unauthorized sales executive creation attempt by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validation for phone number (if provided)
        phone_number = data.get('phone_number')
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
            logger.error(f"Invalid phone number provided by User ID {current_user['id']}.")
            return {'message': 'Invalid phone number. Must be 10 digits.'}, 400

        new_sales_executive = SalesExecutive(
            name=data['name'],
            code=data['code'],
            manager_id=current_user['id'],
            phone_number=phone_number
        )
        db.session.add(new_sales_executive)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sales_executive',
            resource_id=new_sales_executive.id,
            details=f"Manager created a new sales executive with ID {new_sales_executive.id}"
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
        """Update an existing sales executive's details (only self-updates or updates to subordinates)."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            logger.warning(f"Unauthorized update attempt by User ID {current_user['id']} on Sales Executive ID {executive_id}.")
            return {'message': 'Unauthorized'}, 403

        # Allow manager to update only their own details or sales executives they manage
        sales_executive = SalesExecutive.query.filter_by(id=executive_id, is_deleted=False).first()
        if not sales_executive or (sales_executive.manager_id != current_user['id']):
            logger.error(f"Sales Executive ID {executive_id} not found or unauthorized access by User ID {current_user['id']}.")
            return {'message': 'Sales Executive not found or unauthorized'}, 404

        data = request.json

        # Validation for phone number (if provided)
        phone_number = data.get('phone_number')
        if phone_number and (not phone_number.isdigit() or len(phone_number) != 10):
            logger.error(f"Invalid phone number update attempt by User ID {current_user['id']} for Sales Executive ID {executive_id}.")
            return {'message': 'Invalid phone number. Must be 10 digits.'}, 400

        sales_executive.name = data.get('name', sales_executive.name)
        sales_executive.code = data.get('code', sales_executive.code)
        sales_executive.phone_number = phone_number if phone_number else sales_executive.phone_number
        sales_executive.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_executive',
            resource_id=sales_executive.id,
            details=f"Manager updated sales executive with ID {sales_executive.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Sales Executive ID {sales_executive.id} updated by Manager ID {current_user['id']}.")
        return sales_executive.serialize(), 200

    @manager_ns.doc(security='Bearer Auth', responses={403: 'Unauthorized'})
    @jwt_required()
    def delete(self, executive_id):
        """Soft-deletes are not allowed for sales executives."""
        logger.warning(f"Unauthorized delete attempt by User ID {current_user['id']} on Sales Executive ID {executive_id}.")
        return {'message': 'Managers are not authorized to delete sales executives'}, 403
