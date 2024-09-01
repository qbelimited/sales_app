from flask_restful import Resource
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive
from models.sales_model import Sale
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class ManagerResource(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            return {'message': 'Unauthorized'}, 403

        sales_executives = SalesExecutive.query.filter_by(manager_id=current_user['id'], is_deleted=False).all()
        sales_data = Sale.query.filter(Sale.user_id.in_([se.id for se in sales_executives]), Sale.is_deleted == False).all()

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sales_data',
            resource_id=None,
            details=f"Manager accessed sales data"
        )
        db.session.add(audit)
        db.session.commit()

        return jsonify({
            'sales_executives': [se.serialize() for se in sales_executives],
            'sales_data': [sale.serialize() for sale in sales_data]
        })

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_sale = Sale(
            user_id=current_user['id'],
            sale_manager=data['sale_manager'],
            sales_executive_id=data['sales_executive_id'],
            branch_id=data['branch_id'],
            client_phone=data['client_phone'],
            bank_name=data.get('bank_name'),
            bank_branch=data.get('bank_branch'),
            bank_acc_number=data.get('bank_acc_number'),
            amount=data['amount'],
            geolocation=data.get('geolocation')
        )
        db.session.add(new_sale)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sale',
            resource_id=new_sale.id,
            details=f"Manager created a new sale with ID {new_sale.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_sale.serialize(), 201

    @jwt_required()
    def put(self, sale_id):
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            return {'message': 'Unauthorized'}, 403

        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return {'message': 'Sale not found'}, 404

        data = request.json
        sale.sale_manager = data.get('sale_manager', sale.sale_manager)
        sale.sales_executive_id = data.get('sales_executive_id', sale.sales_executive_id)
        sale.branch_id = data.get('branch_id', sale.branch_id)
        sale.client_phone = data.get('client_phone', sale.client_phone)
        sale.bank_name = data.get('bank_name', sale.bank_name)
        sale.bank_branch = data.get('bank_branch', sale.bank_branch)
        sale.bank_acc_number = data.get('bank_acc_number', sale.bank_acc_number)
        sale.amount = data.get('amount', sale.amount)
        sale.updated_at = datetime.utcnow()
        sale.status = 'updated'

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sale',
            resource_id=sale.id,
            details=f"Manager updated sale with ID {sale.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return sale.serialize(), 200
