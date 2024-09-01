from flask_restful import Resource
from flask import request, jsonify
from models.paypoint_model import Paypoint
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class PaypointResource(Resource):
    @jwt_required()
    def get(self, paypoint_id=None):
        current_user = get_jwt_identity()
        if paypoint_id:
            paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
            if not paypoint:
                return {'message': 'Paypoint not found'}, 404

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='paypoint',
                resource_id=paypoint_id,
                details=f"User accessed Paypoint with ID {paypoint_id}"
            )
            db.session.add(audit)
            db.session.commit()

            return paypoint.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            paypoint_query = Paypoint.query.filter_by(is_deleted=False)

            if filter_by:
                paypoint_query = paypoint_query.filter(Paypoint.name.ilike(f'%{filter_by}%'))

            paypoints = paypoint_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='paypoint_list',
                resource_id=None,
                details=f"User accessed list of Paypoints"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'paypoints': [paypoint.serialize() for paypoint in paypoints.items],
                'total': paypoints.total,
                'pages': paypoints.pages,
                'current_page': paypoints.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data = request.json

        new_paypoint = Paypoint(
            name=data['name'],
            location=data['location']
        )
        db.session.add(new_paypoint)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='paypoint',
            resource_id=new_paypoint.id,
            details=f"User created a new Paypoint with ID {new_paypoint.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_paypoint.serialize(), 201

    @jwt_required()
    def put(self, paypoint_id):
        current_user = get_jwt_identity()
        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            return {'message': 'Paypoint not found'}, 404

        data = request.json
        paypoint.name = data.get('name', paypoint.name)
        paypoint.location = data.get('location', paypoint.location)
        paypoint.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='paypoint',
            resource_id=paypoint.id,
            details=f"User updated Paypoint with ID {paypoint.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return paypoint.serialize(), 200

    @jwt_required()
    def delete(self, paypoint_id):
        current_user = get_jwt_identity()
        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            return {'message': 'Paypoint not found'}, 404

        paypoint.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='paypoint',
            resource_id=paypoint.id,
            details=f"User deleted Paypoint with ID {paypoint.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Paypoint deleted successfully'}, 200
