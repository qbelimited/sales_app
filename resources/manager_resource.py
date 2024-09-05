from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from app import db
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
    def get(self):
        """Retrieve all sales executives managed by the current manager."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            return {'message': 'Unauthorized'}, 403

        # Get sales executives under this manager
        sales_executives = SalesExecutive.query.filter_by(manager_id=current_user['id'], is_deleted=False).all()

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
            'sales_executives': [se.serialize() for se in sales_executives]
        })

    @manager_ns.doc(security='Bearer Auth', responses={201: 'Created', 403: 'Unauthorized'})
    @jwt_required()
    @manager_ns.expect(sales_executive_model, validate=True)
    def post(self):
        """Create a new sales executive under the current manager."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_sales_executive = SalesExecutive(
            name=data['name'],
            code=data['code'],
            manager_id=current_user['id'],
            phone_number=data.get('phone_number')
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
            return {'message': 'Unauthorized'}, 403

        # Allow manager to update only their own details or sales executives they manage
        sales_executive = SalesExecutive.query.filter_by(id=executive_id, is_deleted=False).first()
        if not sales_executive or (sales_executive.manager_id != current_user['id'] and sales_executive.id != current_user['id']):
            return {'message': 'Sales Executive not found or unauthorized'}, 404

        data = request.json
        sales_executive.name = data.get('name', sales_executive.name)
        sales_executive.code = data.get('code', sales_executive.code)
        sales_executive.phone_number = data.get('phone_number', sales_executive.phone_number)
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

        return sales_executive.serialize(), 200

    @manager_ns.doc(security='Bearer Auth', responses={403: 'Unauthorized'})
    @jwt_required()
    def delete(self, executive_id):
        """Soft-deletes are not allowed for sales executives."""
        return {'message': 'Managers are not authorized to delete sales executives'}, 403
