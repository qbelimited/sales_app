from flask_restful import Resource
from flask import request, jsonify
from models.sales_model import Sale
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_

class SaleResource(Resource):
    @jwt_required()
    def get(self, sale_id=None):
        current_user = get_jwt_identity()
        if sale_id:
            sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
            if not sale:
                return {'message': 'Sale not found'}, 404
            return sale.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            sales_query = Sale.query.filter_by(is_deleted=False)

            if filter_by:
                sales_query = sales_query.filter(or_(
                    Sale.sale_manager.ilike(f'%{filter_by}%'),
                    Sale.sales_executive.ilike(f'%{filter_by}%')
                ))

            sales = sales_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            return {
                'sales': [sale.serialize() for sale in sales.items],
                'total': sales.total,
                'pages': sales.pages,
                'current_page': sales.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
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

    @jwt_required()
    def delete(self, sale_id):
        current_user = get_jwt_identity()
        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return {'message': 'Sale not found'}, 404

        sale.is_deleted = True
        db.session.commit()

        return {'message': 'Sale deleted successfully'}, 200
