from flask_restful import Resource
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive
from models.sales_model import Sale
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

class ManagerResource(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        if current_user['role'] != 'manager':
            return {'message': 'Unauthorized'}, 403

        sales_executives = SalesExecutive.query.filter_by(manager_id=current_user['id'], is_deleted=False).all()
        sales_data = Sale.query.filter(Sale.user_id.in_([se.id for se in sales_executives]), Sale.is_deleted == False).all()

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
            sales_executive=data['sales_executive'],
            branch=data['branch'],
            telephone=data['telephone'],
            bank_name=data['bank_name'],
            bank_branch=data['bank_branch'],
            bank_acc_number=data['bank_acc_number'],
            amount=data['amount'],
            geolocation=data['geolocation']
        )
        db.session.add(new_sale)
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
        sale.sales_executive = data.get('sales_executive', sale.sales_executive)
        sale.branch = data.get('branch', sale.branch)
        sale.telephone = data.get('telephone', sale.telephone)
        sale.bank_name = data.get('bank_name', sale.bank_name)
        sale.bank_branch = data.get('bank_branch', sale.bank_branch)
        sale.bank_acc_number = data.get('bank_acc_number', sale.bank_acc_number)
        sale.amount = data.get('amount', sale.amount)
        sale.updated_at = datetime.utcnow()
        sale.status = 'updated'

        db.session.commit()

        return sale.serialize(), 200
