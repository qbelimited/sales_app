from flask_restful import Resource
from flask import request, jsonify
from models.audit_model import AuditTrail
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

class AuditTrailResource(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':  # Assuming only admins can view audit logs
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        audit_query = AuditTrail.query

        if filter_by:
            audit_query = audit_query.filter(AuditTrail.details.ilike(f'%{filter_by}%'))

        audits = audit_query.order_by(sort_by).paginate(page, per_page, error_out=False)

        return {
            'audits': [audit.serialize() for audit in audits.items],
            'total': audits.total,
            'pages': audits.pages,
            'current_page': audits.page
        }, 200
