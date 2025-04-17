from flask_restx import Namespace, Resource, fields
from flask import request
from models.under_investigation_model import (
    UnderInvestigation, InvestigationPriority, InvestigationStatus
)
from models.audit_model import AuditTrail
from models.sales_model import Sale
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip
import json
from functools import wraps


# Define namespace
under_inv_ns = Namespace(
    'under_investigations',
    description='Sales investigations management'
)


# Enhanced error handling decorator
def handle_errors(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return {'message': str(e)}, 400
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {'message': 'An unexpected error occurred'}, 500
    return wrapped


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
    'updated_by_user_id': fields.Integer(
        description='User ID of the last user who updated the investigation'
    ),
    'priority': fields.String(
        description=(
            'Investigation priority '
            '(LOW, MEDIUM, HIGH, CRITICAL)'
        )
    ),
    'status': fields.String(
        description=(
            'Investigation status '
            '(OPEN, IN_PROGRESS, PENDING_REVIEW, RESOLVED)'
        )
    ),
    'assigned_to_user_id': fields.Integer(
        description='User ID of the assigned investigator'
    ),
    'estimated_resolution_date': fields.DateTime(
        description='Estimated date of resolution'
    ),
    'risk_score': fields.Float(description='Calculated risk score'),
    'tags': fields.List(fields.String, description='Investigation tags'),
    'category': fields.String(description='Investigation category'),
    'sla_status': fields.String(description='SLA status (on_track, warning, breached)'),
    'custom_fields': fields.Raw(description='Custom fields for the investigation'),
    'attachments': fields.List(fields.Raw, description='Investigation attachments'),
    'related_investigations': fields.List(
        fields.Integer,
        description='Related investigation IDs'
    )
})


# Helper functions for validation
def validate_priority(priority):
    """Validate investigation priority."""
    if not priority:
        return True
    valid_priorities = [p.value for p in InvestigationPriority]
    if priority not in valid_priorities:
        raise ValueError(
            f'Invalid priority value. Must be one of: '
            f'{", ".join(valid_priorities)}'
        )
    return True


def validate_status(status):
    """Validate investigation status."""
    if not status:
        return True
    valid_statuses = [s.value for s in InvestigationStatus]
    if status not in valid_statuses:
        raise ValueError(
            f'Invalid status value. Must be one of: '
            f'{", ".join(valid_statuses)}'
        )
    return True


def validate_sla_dates(estimated_resolution_date):
    """Validate SLA dates."""
    if not estimated_resolution_date:
        return True
    try:
        resolution_date = datetime.fromisoformat(
            estimated_resolution_date.replace("Z", "+00:00")
        )
        if resolution_date <= datetime.utcnow():
            raise ValueError('Estimated resolution date must be in the future')
        return True
    except ValueError as e:
        raise ValueError(f'Invalid date format: {str(e)}')


def validate_custom_fields(custom_fields):
    """Validate custom fields format."""
    if not custom_fields:
        return True
    try:
        if isinstance(custom_fields, str):
            json.loads(custom_fields)
        return True
    except json.JSONDecodeError:
        raise ValueError('Invalid custom fields format. Must be valid JSON')


def validate_related_investigations(related_ids):
    """Validate related investigation IDs."""
    if not related_ids:
        return True
    try:
        if isinstance(related_ids, str):
            related_ids = json.loads(related_ids)
        for inv_id in related_ids:
            if not isinstance(inv_id, int):
                raise ValueError('Related investigation IDs must be integers')
            if not UnderInvestigation.query.get(inv_id):
                raise ValueError(f'Related investigation ID {inv_id} not found')
        return True
    except json.JSONDecodeError:
        raise ValueError('Invalid related investigations format. Must be valid JSON')


def validate_investigation_data(data):
    """Validate all investigation data."""
    errors = []

    # Required fields validation
    required_fields = ['sale_id', 'reason']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f'Missing required field: {field}')

    # Validate sale exists
    if 'sale_id' in data:
        sale = Sale.query.filter_by(id=data['sale_id'], is_deleted=False).first()
        if not sale:
            errors.append(f'Sale ID {data["sale_id"]} not found')

    # Validate optional fields
    try:
        validate_priority(data.get('priority'))
    except ValueError as e:
        errors.append(str(e))

    try:
        validate_status(data.get('status'))
    except ValueError as e:
        errors.append(str(e))

    try:
        validate_sla_dates(data.get('estimated_resolution_date'))
    except ValueError as e:
        errors.append(str(e))

    try:
        validate_custom_fields(data.get('custom_fields'))
    except ValueError as e:
        errors.append(str(e))

    try:
        validate_related_investigations(data.get('related_investigations'))
    except ValueError as e:
        errors.append(str(e))

    if errors:
        raise ValueError('; '.join(errors))


@under_inv_ns.route('/')
class UnderInvestigationListResource(Resource):
    @under_inv_ns.doc(security='Bearer Auth')
    @under_inv_ns.marshal_list_with(under_investigation_model)
    @jwt_required()
    @handle_errors
    def get(self):
        """Retrieve a list of investigations."""
        current_user = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'flagged_at')
        priority = request.args.get('priority', None)
        status = request.args.get('status', None)
        risk_score_min = request.args.get('risk_score_min', None, type=float)
        risk_score_max = request.args.get('risk_score_max', None, type=float)

        try:
            investigation_query = UnderInvestigation.query

            if filter_by:
                investigation_query = investigation_query.filter(
                    UnderInvestigation.reason.ilike(f'%{filter_by}%')
                )

            if priority:
                validate_priority(priority)
                investigation_query = investigation_query.filter_by(priority=priority)

            if status:
                validate_status(status)
                investigation_query = investigation_query.filter_by(status=status)

            if risk_score_min is not None:
                investigation_query = investigation_query.filter(
                    UnderInvestigation.risk_score >= risk_score_min
                )

            if risk_score_max is not None:
                investigation_query = investigation_query.filter(
                    UnderInvestigation.risk_score <= risk_score_max
                )

            investigations = investigation_query.order_by(sort_by).paginate(
                page=page, per_page=per_page, error_out=False
            )

            # Log the access to audit trail
            logger.info(
                f"User {current_user['id']} accessed list of under investigation records"
            )
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='under_investigation_list',
                resource_id=None,
                details="User accessed list of under investigation records",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return investigations.items, 200
        except Exception as e:
            logger.error(f"Error retrieving investigations: {str(e)}")
            raise

    @under_inv_ns.expect(under_investigation_model)
    @under_inv_ns.doc(
        security='Bearer Auth',
        responses={201: 'Created', 400: 'Bad Request'}
    )
    @jwt_required()
    @handle_errors
    def post(self):
        """Flag a new sale as under investigation."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate all investigation data
        validate_investigation_data(data)

        try:
            new_investigation = UnderInvestigation(
                sale_id=data['sale_id'],
                reason=data['reason'],
                notes=data.get('notes', ''),
                flagged_at=datetime.utcnow(),
                resolved=False,
                updated_by_user_id=current_user['id'],
                priority=data.get('priority', InvestigationPriority.MEDIUM.value),
                status=data.get('status', InvestigationStatus.OPEN.value),
                assigned_to_user_id=data.get('assigned_to_user_id'),
                estimated_resolution_date=datetime.fromisoformat(
                    data['estimated_resolution_date'].replace("Z", "+00:00")
                ) if data.get('estimated_resolution_date') else None,
                tags=','.join(data.get('tags', [])),
                category=data.get('category'),
                custom_fields=json.dumps(data.get('custom_fields', {})),
                attachments=json.dumps(data.get('attachments', [])),
                related_investigations=json.dumps(data.get('related_investigations', []))
            )
            db.session.add(new_investigation)
            db.session.commit()

            # Calculate initial risk score
            new_investigation.calculate_risk_score()

            # Log the investigation creation to audit trail
            logger.info(
                f"User {current_user['id']} flagged sale with ID {data['sale_id']} "
                "as under investigation"
            )
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='under_investigation',
                resource_id=new_investigation.id,
                details=(
                    f"User flagged sale with ID {data['sale_id']} "
                    "as under investigation"
                ),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return new_investigation.serialize(), 201
        except Exception as e:
            logger.error(f"Error creating investigation: {str(e)}")
            db.session.rollback()
            raise


@under_inv_ns.route('/<int:investigation_id>')
class UnderInvestigationResource(Resource):
    @under_inv_ns.doc(security='Bearer Auth')
    @under_inv_ns.marshal_with(under_investigation_model)
    @jwt_required()
    @handle_errors
    def get(self, investigation_id):
        """Retrieve a specific investigation by ID."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(
                f"Investigation ID {investigation_id} not found for "
                f"User {current_user['id']}"
            )
            return {'message': 'Investigation not found'}, 404

        try:
            # Update risk score and SLA status
            investigation.calculate_risk_score()
            investigation.update_sla_status()

            # Log the access to audit trail
            logger.info(
                f"User {current_user['id']} accessed investigation with "
                f"ID {investigation_id}"
            )
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
        except Exception as e:
            logger.error(f"Error retrieving investigation: {str(e)}")
            raise

    @under_inv_ns.expect(under_investigation_model)
    @under_inv_ns.doc(
        security='Bearer Auth',
        responses={200: 'Updated', 404: 'Investigation not found'}
    )
    @jwt_required()
    @handle_errors
    def put(self, investigation_id):
        """Update an investigation's status or notes."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(
                f"Investigation ID {investigation_id} not found for "
                f"User {current_user['id']}"
            )
            return {'message': 'Investigation not found'}, 404

        data = request.json

        try:
            # Validate updated data
            validate_investigation_data(data)

            # Update fields
            for key, value in data.items():
                if hasattr(investigation, key):
                    if key in ['custom_fields', 'attachments', 'related_investigations']:
                        setattr(investigation, key, json.dumps(value))
                    elif key == 'estimated_resolution_date':
                        setattr(
                            investigation,
                            key,
                            datetime.fromisoformat(value.replace("Z", "+00:00"))
                        )
                    elif key == 'tags':
                        setattr(investigation, key, ','.join(value))
                    else:
                        setattr(investigation, key, value)

            investigation.updated_by_user_id = current_user['id']
            investigation.calculate_risk_score()
            investigation.update_sla_status()

            db.session.commit()

            # Log the update to audit trail
            logger.info(
                f"User {current_user['id']} updated investigation with "
                f"ID {investigation_id}"
            )
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='under_investigation',
                resource_id=investigation_id,
                details=f"User updated investigation with ID {investigation_id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return investigation.serialize(), 200
        except Exception as e:
            logger.error(f"Error updating investigation: {str(e)}")
            db.session.rollback()
            raise

    @under_inv_ns.doc(
        security='Bearer Auth',
        responses={200: 'Resolved', 404: 'Investigation not found'}
    )
    @jwt_required()
    @handle_errors
    def delete(self, investigation_id):
        """Mark an investigation as resolved."""
        current_user = get_jwt_identity()

        investigation = UnderInvestigation.query.filter_by(id=investigation_id).first()
        if not investigation:
            logger.error(
                f"Investigation ID {investigation_id} not found for "
                f"User {current_user['id']}"
            )
            return {'message': 'Investigation not found'}, 404

        try:
            investigation.resolved = True
            investigation.resolved_at = datetime.utcnow()
            investigation.updated_by_user_id = current_user['id']
            investigation.status = InvestigationStatus.RESOLVED.value

            db.session.commit()

            # Log the resolution to audit trail
            logger.info(
                f"User {current_user['id']} resolved investigation with "
                f"ID {investigation_id}"
            )
            audit = AuditTrail(
                user_id=current_user['id'],
                action='RESOLVE',
                resource_type='under_investigation',
                resource_id=investigation_id,
                details=f"User resolved investigation with ID {investigation_id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': 'Investigation resolved successfully'}, 200
        except Exception as e:
            logger.error(f"Error resolving investigation: {str(e)}")
            db.session.rollback()
            raise


@under_inv_ns.route('/auto-update')
class UpdateUnderInvestigationsResource(Resource):
    @under_inv_ns.doc(
        security='Bearer Auth',
        responses={200: 'Updated', 500: 'Internal Server Error'}
    )
    @jwt_required()
    @handle_errors
    def post(self):
        """Automatically update investigation statuses and risk scores."""
        current_user = get_jwt_identity()

        try:
            investigations = UnderInvestigation.query.filter_by(resolved=False).all()
            updated_count = 0

            for investigation in investigations:
                old_risk_score = investigation.risk_score
                old_sla_status = investigation.sla_status

                investigation.calculate_risk_score()
                investigation.update_sla_status()

                if (old_risk_score != investigation.risk_score or
                        old_sla_status != investigation.sla_status):
                    updated_count += 1

            db.session.commit()

            # Log the auto-update to audit trail
            logger.info(
                f"User {current_user['id']} triggered auto-update of "
                f"{updated_count} investigations"
            )
            audit = AuditTrail(
                user_id=current_user['id'],
                action='AUTO_UPDATE',
                resource_type='under_investigation',
                resource_id=None,
                details=f"Auto-updated {updated_count} investigations",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': f'Updated {updated_count} investigations'}, 200
        except Exception as e:
            logger.error(f"Error auto-updating investigations: {str(e)}")
            db.session.rollback()
            raise
