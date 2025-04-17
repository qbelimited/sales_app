from flask_restx import Namespace, Resource, fields
from flask import request
from models.under_investigation_model import (
    InvestigationSLA, InvestigationPriority, InvestigationCategory
)
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
import json
from datetime import datetime
from functools import wraps

# Define namespace
sla_ns = Namespace('slas', description='Service Level Agreement management')

# Define models for Swagger documentation
sla_model = sla_ns.model('SLA', {
    'id': fields.Integer(description='SLA ID'),
    'name': fields.String(required=True, description='SLA name'),
    'description': fields.String(description='SLA description'),
    'category': fields.String(
        required=True,
        description='Investigation category'
    ),
    'priority': fields.String(
        required=True,
        description='Investigation priority'
    ),
    'target_resolution_days': fields.Integer(
        required=True,
        description='Target resolution days'
    ),
    'warning_threshold_days': fields.Integer(
        required=True,
        description='Warning threshold days'
    ),
    'breach_threshold_days': fields.Integer(
        required=True,
        description='Breach threshold days'
    ),
    'escalation_path': fields.Raw(description='Escalation steps as JSON'),
    'notification_settings': fields.Raw(
        description='Notification rules as JSON'
    ),
    'is_active': fields.Boolean(description='Whether the SLA is active'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})


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


# Helper function to check role permissions
def check_role_permission(current_user):
    return current_user['role'].lower() in ['admin', 'manager']


# Helper function to validate SLA data
def validate_sla_data(data):
    required_fields = [
        'name', 'category', 'priority', 'target_resolution_days',
        'warning_threshold_days', 'breach_threshold_days'
    ]

    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        msg = f'Missing required fields: {", ".join(missing_fields)}'
        raise ValueError(msg)

    # Validate thresholds
    if data['warning_threshold_days'] >= data['breach_threshold_days']:
        raise ValueError('Warning threshold must be less than breach threshold')

    if data['target_resolution_days'] >= data['warning_threshold_days']:
        msg = 'Target resolution days must be less than warning threshold'
        raise ValueError(msg)

    # Validate category and priority
    category = InvestigationCategory.query.filter_by(
        name=data['category']
    ).first()
    if not category:
        raise ValueError('Invalid category')

    priority = InvestigationPriority.query.filter_by(
        name=data['priority']
    ).first()
    if not priority:
        raise ValueError('Invalid priority')

    return category, priority


@sla_ns.route('/')
class SLAListResource(Resource):
    @sla_ns.doc('list_slas')
    @sla_ns.marshal_list_with(sla_model)
    @jwt_required()
    @handle_errors
    def get(self):
        """List all SLAs"""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            return {'message': 'Unauthorized'}, 403

        slas = InvestigationSLA.query.all()

        logger.info(f"User {current_user['id']} accessed SLA list")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sla_list',
            resource_id=None,
            details="User accessed SLA list",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return slas

    @sla_ns.doc('create_sla')
    @sla_ns.expect(sla_model)
    @sla_ns.marshal_with(sla_model)
    @jwt_required()
    @handle_errors
    def post(self):
        """Create a new SLA"""
        current_user = get_jwt_identity()

        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.get_json()
        category, priority = validate_sla_data(data)

        try:
            sla = InvestigationSLA(
                name=data['name'],
                description=data.get('description'),
                category_id=category.id,
                priority_id=priority.id,
                target_resolution_days=data['target_resolution_days'],
                warning_threshold_days=data['warning_threshold_days'],
                breach_threshold_days=data['breach_threshold_days'],
                escalation_path=json.dumps(data.get('escalation_path', {})),
                notification_settings=json.dumps(
                    data.get('notification_settings', {})
                ),
                is_active=data.get('is_active', True)
            )

            db.session.add(sla)
            db.session.commit()

            logger.info(f"User {current_user['id']} created SLA: {sla.name}")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='sla',
                resource_id=sla.id,
                details=f'Created SLA: {sla.name}',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return sla, 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating SLA: {str(e)}")
            return {'message': 'Error creating SLA'}, 500


@sla_ns.route('/<int:sla_id>')
class SLAResource(Resource):
    @sla_ns.doc('get_sla')
    @sla_ns.marshal_with(sla_model)
    @jwt_required()
    def get(self, sla_id):
        """Get a specific SLA"""
        current_user = get_jwt_identity()

        # Only admins and managers can view SLAs
        if not check_role_permission(current_user):
            return {'message': 'Unauthorized'}, 403

        sla = InvestigationSLA.query.get_or_404(sla_id)

        # Log the access to audit trail
        logger.info(f"User {current_user['id']} accessed SLA: {sla.name}")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='sla',
            resource_id=sla_id,
            details=f'Accessed SLA: {sla.name}',
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return sla

    @sla_ns.doc('update_sla')
    @sla_ns.expect(sla_model)
    @sla_ns.marshal_with(sla_model)
    @jwt_required()
    def put(self, sla_id):
        """Update a specific SLA"""
        current_user = get_jwt_identity()

        # Only admins can update SLAs
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.get_json()
        sla = InvestigationSLA.query.get_or_404(sla_id)

        try:
            # Update fields
            for key, value in data.items():
                if hasattr(sla, key):
                    if key in ['escalation_path', 'notification_settings']:
                        setattr(sla, key, json.dumps(value))
                    else:
                        setattr(sla, key, value)

            sla.updated_at = datetime.utcnow()
            db.session.commit()

            # Log audit trail
            logger.info(f"User {current_user['id']} updated SLA: {sla.name}")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='sla',
                resource_id=sla.id,
                details=f'Updated SLA: {sla.name}',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return sla
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating SLA: {str(e)}")
            return {'message': 'Error updating SLA'}, 500

    @sla_ns.doc('delete_sla')
    @jwt_required()
    def delete(self, sla_id):
        """Delete a specific SLA"""
        current_user = get_jwt_identity()

        # Only admins can delete SLAs
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        sla = InvestigationSLA.query.get_or_404(sla_id)

        try:
            db.session.delete(sla)
            db.session.commit()

            # Log audit trail
            logger.info(f"User {current_user['id']} deleted SLA: {sla.name}")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='DELETE',
                resource_type='sla',
                resource_id=sla_id,
                details=f'Deleted SLA: {sla.name}',
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return '', 204
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting SLA: {str(e)}")
            return {'message': 'Error deleting SLA'}, 500


@sla_ns.route('/metrics')
class SLAMetricsResource(Resource):
    @sla_ns.doc(security='Bearer Auth')
    @jwt_required()
    @handle_errors
    def get(self):
        """Get SLA metrics and statistics."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            return {'message': 'Unauthorized'}, 403

        try:
            # Get total SLAs
            total_slas = InvestigationSLA.query.count()
            active_slas = InvestigationSLA.query.filter_by(
                is_active=True
            ).count()

            # Get SLAs by category with percentages
            category_counts = db.session.query(
                InvestigationSLA.category,
                db.func.count(InvestigationSLA.id)
            ).group_by(InvestigationSLA.category).all()

            category_stats = {
                category: {
                    'count': count,
                    'percentage': round(
                        (count / total_slas) * 100, 2
                    ) if total_slas > 0 else 0
                }
                for category, count in category_counts
            }

            # Get SLAs by priority with percentages
            priority_counts = db.session.query(
                InvestigationSLA.priority,
                db.func.count(InvestigationSLA.id)
            ).group_by(InvestigationSLA.priority).all()

            priority_stats = {
                priority: {
                    'count': count,
                    'percentage': round(
                        (count / total_slas) * 100, 2
                    ) if total_slas > 0 else 0
                }
                for priority, count in priority_counts
            }

            # Get average resolution times with standard deviation
            resolution_stats = db.session.query(
                db.func.avg(
                    InvestigationSLA.target_resolution_days
                ).label('avg_target'),
                db.func.stddev(
                    InvestigationSLA.target_resolution_days
                ).label('std_target'),
                db.func.avg(
                    InvestigationSLA.warning_threshold_days
                ).label('avg_warning'),
                db.func.stddev(
                    InvestigationSLA.warning_threshold_days
                ).label('std_warning'),
                db.func.avg(
                    InvestigationSLA.breach_threshold_days
                ).label('avg_breach'),
                db.func.stddev(
                    InvestigationSLA.breach_threshold_days
                ).label('std_breach')
            ).first()

            metrics = {
                'total_slas': total_slas,
                'active_slas': active_slas,
                'inactive_slas': total_slas - active_slas,
                'category_stats': category_stats,
                'priority_stats': priority_stats,
                'resolution_times': {
                    'target': {
                        'average': round(
                            resolution_stats.avg_target or 0, 2
                        ),
                        'standard_deviation': round(
                            resolution_stats.std_target or 0, 2
                        )
                    },
                    'warning': {
                        'average': round(
                            resolution_stats.avg_warning or 0, 2
                        ),
                        'standard_deviation': round(
                            resolution_stats.std_warning or 0, 2
                        )
                    },
                    'breach': {
                        'average': round(
                            resolution_stats.avg_breach or 0, 2
                        ),
                        'standard_deviation': round(
                            resolution_stats.std_breach or 0, 2
                        )
                    }
                }
            }

            logger.info(f"User {current_user['id']} accessed SLA metrics")
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='sla_metrics',
                resource_id=None,
                details="User accessed SLA metrics",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return metrics, 200
        except Exception as e:
            logger.error(f"Error getting SLA metrics: {str(e)}")
            return {'message': 'Error getting SLA metrics'}, 500
