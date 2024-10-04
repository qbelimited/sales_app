from flask_restx import Namespace, Resource, fields
from flask import request
from models.under_investigation_model import UnderInvestigation
from models.audit_model import AuditTrail
from models.sales_model import Sale
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip

# Define namespace
under_inv_ns = Namespace('under_investigations', description='Sales investigations management')

# Define models for Swagger documentation
under_investigation_model = under_inv_ns.model('UnderInvestigation', {
    'id': fields.Integer(description='Investigation ID'),
    'sale_id': fields.Integer(required=True, description='Sale ID under investigation'),
    'reason': fields.String(required=True, description='Reason for the investigation'),
    'notes': fields.String(description='Additional notes'),
    'notes_history': fields.String(description='Notes History'),
    'flagged_at': fields.DateTime(description='Time the sale was flagged'),
    'resolved': fields.Boolean(description='Whether the investigation is resolved'),
    'resolved_at': fields.DateTime(description='Time the investigation was resolved'),
    'updated_by_user_id': fields.Integer(description='User ID of the last user who updated the investigation')
})

@under_inv_ns.route('/')
class UnderInvestigationListResource(Resource):
    @under_inv_ns.doc(security='Bearer Auth')
    @under_inv_ns.marshal_list_with(under_investigation_model)
    @jwt_required()
    def get(self):
        """Retrieve a list of investigations."""
        current_user = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'flagged_at')

        investigation_query = UnderInvestigation.query

        if filter_by:
            investigation_query = investigation_query.filter(UnderInvestigation.reason.ilike(f'%{filter_by}%'))

        investigations = investigation_query.order_by(sort_by).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        logger.info(f"User {current_user['id']} accessed list of under investigation records")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='under_investigation_list',
            resource_id=None,
            details=f"User accessed list of under investigation records",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
            if field not in data or not data[field]:
                logger.error(f"Missing required field: {field} by User {current_user['id']}")
                return {'message': f'Missing required field: {field}'}, 400

        sale = Sale.query.filter_by(id=data['sale_id'], is_deleted=False).first()
        if not sale:
            logger.error(f"Sale ID {data['sale_id']} not found for User {current_user['id']}")
            return {'message': 'Sale not found'}, 404

        try:
            new_investigation = UnderInvestigation(
                sale_id=data['sale_id'],
                reason=data['reason'],
                notes=data.get('notes', ''),
                flagged_at=datetime.utcnow(),
                resolved=False,
                updated_by_user_id=current_user['id']  # Add updated_by_user_id on creation
            )
            db.session.add(new_investigation)
            db.session.commit()

            # Log the investigation creation to audit trail
            logger.info(f"User {current_user['id']} flagged sale with ID {data['sale_id']} as under investigation")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='under_investigation',
                resource_id=new_investigation.id,
                details=f"User flagged sale with ID {data['sale_id']} as under investigation",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return new_investigation.serialize(), 201
        except Exception as e:
            logger.error(f"Error creating investigation: {str(e)}")
            db.session.rollback()
            return {'message': 'Error creating investigation'}, 500


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

        # Log the access to audit trail
        logger.info(f"User {current_user['id']} accessed investigation with ID {investigation_id}")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='under_investigation',
            resource_id=investigation_id,
            details=f"User accessed investigation with ID {investigation_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
        try:
            investigation.reason = data.get('reason', investigation.reason)
            if 'notes' in data:
                investigation.add_note_with_history(data['notes'], current_user['id'])
            investigation.resolved = data.get('resolved', investigation.resolved)
            investigation.resolved_at = datetime.utcnow() if investigation.resolved else None

            # Update the updated_by_user_id field
            investigation.updated_by_user_id = current_user['id']

            db.session.commit()

            # Log the investigation update to audit trail
            logger.info(f"User {current_user['id']} updated investigation with ID {investigation.id}")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='under_investigation',
                resource_id=investigation.id,
                details=f"User updated investigation with ID {investigation.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return investigation.serialize(), 200
        except Exception as e:
            logger.error(f"Error updating investigation: {str(e)}")
            db.session.rollback()
            return {'message': 'Error updating investigation'}, 500

    @under_inv_ns.doc(security='Bearer Auth', responses={200: 'Resolved', 404: 'Investigation not found'})
    @jwt_required()
    def delete(self, investigation_id):
        """Resolve and close an investigation."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(f"Investigation ID {investigation_id} not found for User {current_user['id']}")
            return {'message': 'Investigation not found'}, 404

        try:
            investigation.resolved = True
            investigation.resolved_at = datetime.utcnow()
            db.session.commit()

            # Log the investigation resolution to audit trail
            logger.info(f"User {current_user['id']} resolved investigation with ID {investigation.id}")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='under_investigation',
                resource_id=investigation.id,
                details=f"User resolved investigation with ID {investigation.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': 'Investigation resolved successfully'}, 200
        except Exception as e:
            logger.error(f"Error resolving investigation: {str(e)}")
            db.session.rollback()
            return {'message': 'Error resolving investigation'}, 500

@under_inv_ns.route('/auto-update')
class UpdateUnderInvestigationsResource(Resource):
    @under_inv_ns.doc(security='Bearer Auth', responses={200: 'Updated', 500: 'Internal Server Error'})
    @jwt_required()
    def post(self):
        """Update all investigations and related sales statuses."""
        current_user = get_jwt_identity()
        try:
            # Fetch all under investigation records that are not resolved
            investigations = UnderInvestigation.query.filter_by(resolved=False).all()
            sales_to_update = []
            investigations_to_delete = []
            investigations_to_resolve = []

            # Process each investigation
            for investigation in investigations:
                sale = Sale.query.filter_by(id=investigation.sale_id, is_deleted=False).first()

                if sale:
                    # Check for critical and potential duplicates
                    critical_duplicates = sale.find_duplicate(critical=True)
                    potential_duplicates = sale.find_duplicate(critical=False)

                    if critical_duplicates or potential_duplicates:
                        sale.status = 'under investigation'
                        logger.info(f"Sale ID {sale.id} remains under investigation.")
                        sales_to_update.append(sale)
                    else:
                        # No duplicates found, mark as submitted
                        sale.status = 'submitted'
                        investigations_to_resolve.append(investigation)
                        investigation.resolved = True
                        investigation.resolved_at = datetime.utcnow()
                        investigation.notes = f"Sale ID {sale.id} was wrongly flagged system corrected and sale status marked as submitted."
                        logger.info(f"Sale ID {sale.id} was wrongly flagged system corrected and sale status updated to submitted and investigation resolved.")
                        sales_to_update.append(sale)
                else:
                    # Sale does not exist, mark for deletion
                    logger.warning(f"Sale ID {investigation.sale_id} does not exist. Marking investigation for deletion.")
                    investigations_to_delete.append(investigation)

            # Commit updates to sales
            for sale in sales_to_update:
                db.session.add(sale)

            # Commit resolutions
            for investigation in investigations_to_resolve:
                db.session.add(investigation)

            # Permanent delete investigations that are no longer relevant
            for investigation in investigations_to_delete:
                db.session.delete(investigation)

            # Commit all changes at once
            db.session.commit()

            # Audit Trail: Log the updates
            for sale in sales_to_update:
                audit = AuditTrail(
                    user_id=current_user['id'],
                    action='UPDATE',
                    resource_type='sale',
                    resource_id=sale.id,
                    details=f"Sale ID {sale.id} was wrongly flagged system corrected and sale status updated to {sale.status}.",
                    ip_address=get_client_ip(),
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit)

            for investigation in investigations_to_resolve:
                audit = AuditTrail(
                    user_id=current_user['id'],
                    action='UPDATE',
                    resource_type='under_investigation',
                    resource_id=investigation.id,
                    details=f"Investigation for Sale ID {investigation.sale_id} resolved.",
                    ip_address=get_client_ip(),
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit)

            for investigation in investigations_to_delete:
                audit = AuditTrail(
                    user_id=current_user['id'],
                    action='DELETE',
                    resource_type='under_investigation',
                    resource_id=investigation.id,
                    details=f"Investigation for Sale ID {investigation.sale_id} deleted.",
                    ip_address=get_client_ip(),
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit)

            db.session.commit()  # Commit the audit trail entries

            return {'message': 'Investigations and sales statuses updated successfully'}, 200
        except Exception as e:
            logger.error(f"Error updating investigations: {str(e)}")
            db.session.rollback()
            return {'message': 'Error updating investigations'}, 500
