from flask_restful import Resource
from flask import request, jsonify
from models.bank_model import Bank, Branch
from models.sales_executive_model import SalesExecutive
from app import db

class DropdownResource(Resource):
    def get(self):
        dropdown_type = request.args.get('type')
        response = []

        if dropdown_type == 'bank':
            banks = Bank.query.all()
            response = [bank.serialize() for bank in banks]

        elif dropdown_type == 'branch':
            bank_id = request.args.get('bank_id')
            branches = Branch.query.filter_by(bank_id=bank_id).all()
            response = [branch.serialize() for branch in branches]

        elif dropdown_type == 'sales_executive':
            manager_id = request.args.get('manager_id')
            sales_executives = SalesExecutive.query.filter_by(manager_id=manager_id).all()
            response = [se.serialize() for se in sales_executives]

        return jsonify(response)
