from flask_restful import Resource
from flask import request, jsonify
from models.user_model import User
from models.sales_executive_model import SalesExecutive
from models.bank_model import Bank, Branch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail
from app import db

class AdminResource(Resource):
    def get(self):
        users = User.query.all()
        sales_executives = SalesExecutive.query.all()
        banks = Bank.query.all()
        branches = Branch.query.all()
        paypoints = Paypoint.query.all()
        products = ImpactProduct.query.all()

        return jsonify({
            'users': [user.serialize() for user in users],
            'sales_executives': [se.serialize() for se in sales_executives],
            'banks': [bank.serialize() for bank in banks],
            'branches': [branch.serialize() for branch in branches],
            'paypoints': [paypoint.serialize() for paypoint in paypoints],
            'products': [product.serialize() for product in products]
        })

    def post(self):
        data = request.json
        if data['type'] == 'sales_executive':
            new_sales_executive = SalesExecutive(
                name=data['name'],
                code=data['code'],
                manager_id=data['manager_id'],
                branch_id=data['branch_id']
            )
            db.session.add(new_sales_executive)
        elif data['type'] == 'bank':
            new_bank = Bank(name=data['name'])
            db.session.add(new_bank)
        elif data['type'] == 'branch':
            new_branch = Branch(name=data['name'], bank_id=data['bank_id'])
            db.session.add(new_branch)
        elif data['type'] == 'paypoint':
            new_paypoint = Paypoint(name=data['name'], location=data['location'])
            db.session.add(new_paypoint)
        elif data['type'] == 'product':
            new_product = ImpactProduct(name=data['name'], category=data['category'])
            db.session.add(new_product)
        db.session.commit()

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=request.json['user_id'],
            action='CREATE',
            resource_type=data['type'],
            resource_id=db.session.identity_map.get(list(db.session.identity_map.keys())[-1]).id,
            details=f"Created {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Resource added successfully'}, 201

    def put(self):
        data = request.json
        if data['type'] == 'sales_executive':
            se = SalesExecutive.query.get(data['id'])
            se.name = data.get('name', se.name)
            se.code = data.get('code', se.code)
            se.manager_id = data.get('manager_id', se.manager_id)
            se.branch_id = data.get('branch_id', se.branch_id)
        elif data['type'] == 'bank':
            bank = Bank.query.get(data['id'])
            bank.name = data.get('name', bank.name)
        elif data['type'] == 'branch':
            branch = Branch.query.get(data['id'])
            branch.name = data.get('name', branch.name)
            branch.bank_id = data.get('bank_id', branch.bank_id)
        elif data['type'] == 'paypoint':
            paypoint = Paypoint.query.get(data['id'])
            paypoint.name = data.get('name', paypoint.name)
            paypoint.location = data.get('location', paypoint.location)
        elif data['type'] == 'product':
            product = ImpactProduct.query.get(data['id'])
            product.name = data.get('name', product.name)
            product.category = data.get('category', product.category)
        db.session.commit()

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=request.json['user_id'],
            action='UPDATE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Updated {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Resource updated successfully'}, 200

    def delete(self):
        data = request.json
        if data['type'] == 'sales_executive':
            se = SalesExecutive.query.get(data['id'])
            db.session.delete(se)
        elif data['type'] == 'bank':
            bank = Bank.query.get(data['id'])
            db.session.delete(bank)
        elif data['type'] == 'branch':
            branch = Branch.query.get(data['id'])
            db.session.delete(branch)
        elif data['type'] == 'paypoint':
            paypoint = Paypoint.query.get(data['id'])
            db.session.delete(paypoint)
        elif data['type'] == 'product':
            product = ImpactProduct.query.get(data['id'])
            db.session.delete(product)
        db.session.commit()

        # Log the action to audit trail
        audit = AuditTrail(
            user_id=request.json['user_id'],
            action='DELETE',
            resource_type=data['type'],
            resource_id=data['id'],
            details=f"Deleted {data['type']} with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Resource deleted successfully'}, 200
