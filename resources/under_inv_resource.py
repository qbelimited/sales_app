from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.under_investigation_model import UnderInvestigation
from models.audit_model import AuditTrail
from models.sales_model import Sale
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define namespace
under_inv_ns = Namespace('under_investigations', description='Sales investigations management')

# Define models for Swagger documentation
under_investigation_model = under_inv_ns.model('UnderInvestigation', {
    'id': fields.Integer(description='Investigation ID'),
    'sale_id': fields.Integer(required=True, description='Sale ID under investigation'),
    'reason': fields.String(required=True, description='Reason for the investigation'),
    'notes': fields.String(description='Additional notes'),
    'flagged_at': fields.DateTime(description='Time the sale was flagged'),
    'resolved': fields.Boolean(description='Whether the investigation is resolved'),
    'resolved_at': fields.DateTime(description='Time the investigation was resolved')
})

@under_inv_ns.route('/')
class UnderInvestigationListResource(Resource):
    @under_inv_ns.doc(security='Bearer Auth')
    @under_inv_ns.marshal_list_with(under_investigation_model)
    @jwt_required()
    def get(self):
        """Retrieve list of investigations."""
        current_user = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'flagged_at')

        investigation_query = UnderInvestigation.query

        if filter_by:
            investigation_query = investigation_query.filter(UnderInvestigation.reason.ilike(f'%{filter_by}%'))

        investigations = investigation_query.order_by(sort_by).paginate(page, per_page, error_out=False)

        # Log the access to audit trail and logger
        logger.info(f"User {current_user['id']} accessed list of under investigation records")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='under_investigation_list',
            resource_id=None,
            details=f"User accessed list of under investigation records"
        )
        db.session.add(audit)
        db.session.commit()

        return investigations.items, 200

    @under_inv_ns.expect(under_investigation_model)
    @under_inv_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Bad Request'})
    @jwt_required()
    def post(self):
        """Flag a new sale as under investigation."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate required fields
        required_fields = ['sale_id', 'reason']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field} by User {current_user['id']}")
                return {'message': f'Missing required field: {field}'}, 400

        sale = Sale.query.filter_by(id=data['sale_id'], is_deleted=False).first()
        if not sale:
            logger.error(f"Sale ID {data['sale_id']} not found for User {current_user['id']}")
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

        # Log the investigation creation to audit trail and logger
        logger.info(f"User {current_user['id']} flagged sale with ID {data['sale_id']} as under investigation")
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

@under_inv_ns.route('/<int:investigation_id>')
class UnderInvestigationResource(Resource):
    @under_inv_ns.doc(security='Bearer Auth')
    @under_inv_ns.marshal_with(under_investigation_model)
    @jwt_required()
    def get(self, investigation_id):
        """Retrieve a specific investigation by ID."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(f"Investigation ID {investigation_id} not found for User {current_user['id']}")
            return {'message': 'Investigation not found'}, 404

        # Log the access to audit trail and logger
        logger.info(f"User {current_user['id']} accessed investigation with ID {investigation_id}")
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

    @under_inv_ns.expect(under_investigation_model)
    @under_inv_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Investigation not found'})
    @jwt_required()
    def put(self, investigation_id):
        """Update an investigation's status or notes."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(f"Investigation ID {investigation_id} not found for User {current_user['id']}")
            return {'message': 'Investigation not found'}, 404

        data = request.json
        investigation.reason = data.get('reason', investigation.reason)
        investigation.notes = data.get('notes', investigation.notes)
        investigation.resolved = data.get('resolved', investigation.resolved)
        investigation.resolved_at = datetime.utcnow() if investigation.resolved else None
        investigation.updated_by_user_id = current_user['id']

        db.session.commit()

        # Log the investigation update to audit trail and logger
        logger.info(f"User {current_user['id']} updated investigation with ID {investigation.id}")
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

    @under_inv_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Investigation not found'})
    @jwt_required()
    def delete(self, investigation_id):
        """Resolve and delete an investigation."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(f"Investigation ID {investigation_id} not found for User {current_user['id']}")
            return {'message': 'Investigation not found'}, 404

        investigation.resolved = True
        investigation.resolved_at = datetime.utcnow()
        db.session.commit()

        # Log the investigation resolution to audit trail and logger
        logger.info(f"User {current_user['id']} resolved and closed investigation with ID {investigation.id}")
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
