from flask_restful import Resource
from flask import request, jsonify
from models.under_investigation_model import UnderInvestigation
from models.audit_model import AuditTrail
from models.sales_model import Sale
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class UnderInvestigationResource(Resource):
    @jwt_required()
    def get(self, investigation_id=None):
        """Retrieve investigation details or list of investigations."""
        current_user = get_jwt_identity()

        if investigation_id:
            investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
            if not investigation:
                return {'message': 'Investigation not found'}, 404

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='under_investigation',
                resource_id=investigation_id,
                details=f"User accessed investigation with ID {investigation_id}"
            )
            db.session.add(audit)
            db.session.commit()

            return investigation.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'flagged_at')

            investigation_query = UnderInvestigation.query

            if filter_by:
                investigation_query = investigation_query.filter(UnderInvestigation.reason.ilike(f'%{filter_by}%'))

            investigations = investigation_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='under_investigation_list',
                resource_id=None,
                details=f"User accessed list of under investigation records"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'investigations': [investigation.serialize() for investigation in investigations.items],
                'total': investigations.total,
                'pages': investigations.pages,
                'current_page': investigations.page
            }, 200

    @jwt_required()
    def post(self):
        """Flag a new sale as under investigation."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate required fields
        required_fields = ['sale_id', 'reason']
        for field in required_fields:
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400

        sale = Sale.query.filter_by(id=data['sale_id'], is_deleted=False).first()
        if not sale:
            return {'message': 'Sale not found'}, 404

        new_investigation = UnderInvestigation(
            sale_id=data['sale_id'],
            reason=data['reason'],
            notes=data.get('notes', ''),
            flagged_at=datetime.utcnow(),
            resolved=False
        )
        db.session.add(new_investigation)
        db.session.commit()

        # Log the investigation creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='under_investigation',
            resource_id=new_investigation.id,
            details=f"User flagged sale with ID {data['sale_id']} as under investigation"
        )
        db.session.add(audit)
        db.session.commit()

        return new_investigation.serialize(), 201

    @jwt_required()
    def put(self, investigation_id):
        """Update an investigation's status or notes."""
        current_user = get_jwt_identity()
        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            return {'message': 'Investigation not found'}, 404

        data = request.json
        investigation.reason = data.get('reason', investigation.reason)
        investigation.notes = data.get('notes', investigation.notes)
        investigation.resolved = data.get('resolved', investigation.resolved)
        investigation.resolved_at = datetime.utcnow() if investigation.resolved else None
        investigation.updated_by_user_id = current_user['id']

        db.session.commit()

        # Log the investigation update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='under_investigation',
            resource_id=investigation.id,
            details=f"User updated investigation with ID {investigation.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return investigation.serialize(), 200

    @jwt_required()
    def delete(self, investigation_id):
        """Resolve and delete an investigation."""
        current_user = get_jwt_identity()
        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            return {'message': 'Investigation not found'}, 404

        investigation.resolved = True
        investigation.resolved_at = datetime.utcnow()
        db.session.commit()

        # Log the investigation resolution in audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='under_investigation',
            resource_id=investigation.id,
            details=f"User resolved and closed investigation with ID {investigation.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Investigation resolved and closed successfully'}, 200
