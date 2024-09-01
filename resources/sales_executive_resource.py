from flask_restful import Resource
from flask import request, jsonify
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class SalesExecutiveResource(Resource):
    @jwt_required()
    def get(self, sales_executive_id=None):
        current_user = get_jwt_identity()
        if sales_executive_id:
            sales_executive = SalesExecutive.query.filter_by(id=sales_executive_id, is_deleted=False).first()
            if not sales_executive:
                return {'message': 'Sales Executive not found'}, 404

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='sales_executive',
                resource_id=sales_executive_id,
                details=f"User accessed Sales Executive with ID {sales_executive_id}"
            )
            db.session.add(audit)
            db.session.commit()

            return sales_executive.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            sales_executive_query = SalesExecutive.query.filter_by(is_deleted=False)

            if filter_by:
                sales_executive_query = sales_executive_query.filter(SalesExecutive.name.ilike(f'%{filter_by}%'))

            sales_executives = sales_executive_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='sales_executive_list',
                resource_id=None,
                details=f"User accessed list of Sales Executives"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'sales_executives': [se.serialize() for se in sales_executives.items],
                'total': sales_executives.total,
                'pages': sales_executives.pages,
                'current_page': sales_executives.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data = request.json

        new_sales_executive = SalesExecutive(
            name=data['name'],
            code=data['code'],
            manager_id=data['manager_id'],
            branch_id=data['branch_id']
        )
        db.session.add(new_sales_executive)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='sales_executive',
            resource_id=new_sales_executive.id,
            details=f"User created a new Sales Executive with ID {new_sales_executive.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_sales_executive.serialize(), 201

    @jwt_required()
    def put(self, sales_executive_id):
        current_user = get_jwt_identity()
        sales_executive = SalesExecutive.query.filter_by(id=sales_executive_id, is_deleted=False).first()
        if not sales_executive:
            return {'message': 'Sales Executive not found'}, 404

        data = request.json
        sales_executive.name = data.get('name', sales_executive.name)
        sales_executive.code = data.get('code', sales_executive.code)
        sales_executive.manager_id = data.get('manager_id', sales_executive.manager_id)
        sales_executive.branch_id = data.get('branch_id', sales_executive.branch_id)
        sales_executive.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='sales_executive',
            resource_id=sales_executive.id,
            details=f"User updated Sales Executive with ID {sales_executive.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return sales_executive.serialize(), 200

    @jwt_required()
    def delete(self, sales_executive_id):
        current_user = get_jwt_identity()
        sales_executive = SalesExecutive.query.filter_by(id=sales_executive_id, is_deleted=False).first()
        if not sales_executive:
            return {'message': 'Sales Executive not found'}, 404

        sales_executive.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='sales_executive',
            resource_id=sales_executive.id,
            details=f"User deleted Sales Executive with ID {sales_executive.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Sales Executive deleted successfully'}, 200
