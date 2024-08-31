from flask_restful import Resource
from flask import request, jsonify
from models.sales_model import Sale
from app import db

class SaleResource(Resource):
    def get(self, sale_id=None):
        if sale_id:
            sale = Sale.query.get(sale_id)
            if not sale:
                return {'message': 'Sale not found'}, 404
            return sale.serialize(), 200
        else:
            sales = Sale.query.all()
            return jsonify([sale.serialize() for sale in sales])

    def post(self):
        data = request.json
        new_sale = Sale(
            user_id=data['user_id'],
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

    def put(self, sale_id):
        sale = Sale.query.get(sale_id)
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
