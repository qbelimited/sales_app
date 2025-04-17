from flask_restx import Namespace, Resource, fields
from flask import request
from models.audit_model import AuditTrail, AuditAction
from app import logger, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
from datetime import datetime, timedelta
from functools import wraps
import time
import psutil
from sqlalchemy import desc, and_

# Define namespace for audit trails
audit_ns = Namespace('audit_trail', description='Audit trail operations')

# Define models for Swagger documentation
audit_model = audit_ns.model('AuditTrail', {
    'id': fields.Integer(description='Audit ID'),
    'user_id': fields.Integer(
        required=True,
        description='User ID who performed the action'
    ),
    'action': fields.String(
        required=True,
        description='Action performed (CREATE, UPDATE, DELETE, etc.)'
    ),
    'resource_type': fields.String(
        required=True,
        description='The type of resource affected (e.g., "role", "user")'
    ),
    'resource_id': fields.Integer(
        description='The ID of the resource affected'
    ),
    'old_value': fields.String(
        description='The previous value before the action'
    ),
    'new_value': fields.String(
        description='The new value after the action'
    ),
    'timestamp': fields.DateTime(
        description='When the action occurred'
    ),
    'details': fields.String(
        description='Additional details about the action'
    ),
    'ip_address': fields.String(
        description='IP address of the user'
    ),
    'user_agent': fields.String(
        description='User agent of the user'
    ),
    'is_archived': fields.Boolean(
        description='Whether the log is archived'
    ),
    'archived_at': fields.DateTime(
        description='When the log was archived'
    )
})

action_summary_model = audit_ns.model('ActionSummary', {
    'action': fields.String(description='Type of action'),
    'count': fields.Integer(description='Number of occurrences')
})

# Performance metrics decorator
def track_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss

        result = func(*args, **kwargs)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss

        execution_time = end_time - start_time
        memory_used = end_memory - start_memory

        logger.info(
            f"Performance metrics for {func.__name__}: "
            f"Execution time: {execution_time:.2f}s, "
            f"Memory used: {memory_used / 1024 / 1024:.2f}MB"
        )

        return result
    return wrapper

# Admin-only decorator
def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(
                f"Unauthorized access attempt by user ID {current_user['id']}"
            )
            return {'message': 'Unauthorized'}, 403
        return func(*args, **kwargs)
    return wrapper

@audit_ns.route('/')
class AuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @audit_ns.marshal_list_with(audit_model)
    @jwt_required()
    @admin_required
    @track_performance
    def get(self):
        """Get the audit trail logs with pagination and filtering."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Optional query parameters to filter the logs
        user_id = request.args.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        resource_type = request.args.get('resource_type')
        action = request.args.get('action')
        include_archived = request.args.get(
            'include_archived', 'false'
        ).lower() == 'true'

        query = AuditTrail.query

        # Filter by user ID if provided
        if user_id:
            query = query.filter(AuditTrail.user_id == user_id)

        # Filter by date range if provided
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AuditTrail.timestamp >= start_dt)
            except ValueError:
                logger.error(
                    f"Invalid start date format for filtering: {start_date}"
                )
                return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(AuditTrail.timestamp <= end_dt)
            except ValueError:
                logger.error(
                    f"Invalid end date format for filtering: {end_date}"
                )
                return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        # Filter by resource type (case-insensitive, partial match)
        if resource_type:
            query = query.filter(
                AuditTrail.resource_type.ilike(f"%{resource_type}%")
            )

        # Filter by action (case-insensitive, partial match)
        if action:
            if action.upper() in AuditAction.__members__:
                query = query.filter(
                    AuditTrail.action.ilike(f"%{action.upper()}%")
                )
            else:
                logger.error(f"Invalid action type provided: {action}")
                return {
                    'message': (
                        f"Invalid action type. Valid types are: "
                        f"{', '.join(AuditAction.__members__.keys())}"
                    )
                }, 400

        # Filter by archived status
        if not include_archived:
            query = query.filter(AuditTrail.is_archived.is_(False))

        # Order by timestamp and paginate
        audit_trails = query.order_by(desc(AuditTrail.timestamp)).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Log the query
        logger.info(
            f"Audit trail query executed: page={page}, per_page={per_page}, "
            f"filters={{user_id: {user_id}, start_date: {start_date}, "
            f"end_date: {end_date}, resource_type: {resource_type}, "
            f"action: {action}, include_archived: {include_archived}}}"
        )

        return {
            'items': [trail.serialize() for trail in audit_trails.items],
            'total': audit_trails.total,
            'pages': audit_trails.pages,
            'current_page': audit_trails.page
        }, 200

@audit_ns.route('/<int:audit_id>')
class SingleAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @audit_ns.response(200, 'Success', audit_model)
    @audit_ns.response(404, 'Audit log not found')
    @jwt_required()
    @admin_required
    @track_performance
    def get(self, audit_id):
        """Retrieve a specific audit log by its ID."""
        audit_log = AuditTrail.query.filter_by(id=audit_id).first()

        if not audit_log:
            logger.error(f"Audit log ID {audit_id} not found")
            return {'message': 'Audit log not found'}, 404

        logger.info(f"Audit log ID {audit_id} retrieved successfully")
        return audit_log.serialize(), 200

@audit_ns.route('/filter')
class FilteredAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    @track_performance
    @audit_ns.marshal_list_with(audit_model)
    def post(self):
        """Filter the audit logs with advanced options."""
        data = request.get_json()

        page = data.get('page', 1)
        per_page = data.get('per_page', 50)
        resource_type = data.get('resource_type')
        action = data.get('action')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        include_archived = data.get('include_archived', False)
        user_id = data.get('user_id')

        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            query = AuditTrail.query

            # Apply filters
            if resource_type:
                query = query.filter(
                    AuditTrail.resource_type.ilike(f"%{resource_type}%")
                )

            if action and action.upper() in AuditAction.__members__:
                query = query.filter(
                    AuditTrail.action.ilike(f"%{action.upper()}%")
                )

            if start_date:
                query = query.filter(AuditTrail.timestamp >= start_date)
            if end_date:
                query = query.filter(AuditTrail.timestamp <= end_date)

            if user_id:
                query = query.filter(AuditTrail.user_id == user_id)

            if not include_archived:
                query = query.filter(AuditTrail.is_archived.is_(False))

            # Order and paginate
            audit_trails = query.order_by(desc(AuditTrail.timestamp)).paginate(
                page=page, per_page=per_page, error_out=False
            )

            return {
                'items': [trail.serialize() for trail in audit_trails.items],
                'total': audit_trails.total,
                'pages': audit_trails.pages,
                'current_page': audit_trails.page
            }, 200
        except ValueError as e:
            logger.error(f"Invalid date format in filter: {e}")
            return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400
        except Exception as e:
            logger.error(f"Error filtering audit logs: {e}")
            return {'message': 'Internal server error'}, 500

@audit_ns.route('/archive')
class ArchiveAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    @track_performance
    def post(self):
        """Archive audit logs older than specified days."""
        data = request.get_json()
        days = data.get('days', 90)  # Default to 90 days

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            logs_to_archive = AuditTrail.query.filter(
                and_(
                    AuditTrail.timestamp < cutoff_date,
                    AuditTrail.is_archived.is_(False)
                )
            ).all()

            for log in logs_to_archive:
                log.is_archived = True
                log.archived_at = datetime.utcnow()

            db.session.commit()

            # Log the archiving action
            AuditTrail.log_action(
                user_id=get_jwt_identity()['id'],
                action=AuditAction.UPDATE,
                resource_type='audit_trail',
                details=(
                    f"Archived {len(logs_to_archive)} audit logs "
                    f"older than {days} days"
                ),
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )

            return {
                'message': (
                    f'Successfully archived {len(logs_to_archive)} logs'
                ),
                'archived_count': len(logs_to_archive)
            }, 200
        except Exception as e:
            logger.error(f"Error archiving audit logs: {e}")
            db.session.rollback()
            return {'message': 'Error archiving audit logs'}, 500

@audit_ns.route('/summary')
class AuditSummaryResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    @track_performance
    def get(self):
        """Get summary statistics of audit actions."""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            summary = AuditTrail.get_action_summary(start_date, end_date)
            return {'summary': summary}, 200
        except ValueError as e:
            logger.error(f"Error getting audit summary: {e}")
            return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400
        except Exception as e:
            logger.error(f"Error getting audit summary: {e}")
            return {'message': 'Internal server error'}, 500

@audit_ns.route('/user/<int:user_id>')
class UserAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    @track_performance
    @audit_ns.marshal_list_with(audit_model)
    def get(self, user_id):
        """Get audit logs for a specific user."""
        include_archived = request.args.get(
            'include_archived', 'false'
        ).lower() == 'true'

        try:
            logs = AuditTrail.get_logs_by_user(user_id, include_archived)
            return logs, 200
        except Exception as e:
            logger.error(f"Error getting user audit logs: {e}")
            return {'message': 'Internal server error'}, 500

@audit_ns.route('/cleanup')
class CleanupAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @admin_required
    @track_performance
    def post(self):
        """Clean up archived audit logs older than specified days."""
        data = request.get_json()
        days = data.get('days', 365)

        try:
            deleted_count = AuditTrail.cleanup_archived_logs(days)
            return {
                'message': f'Successfully deleted {deleted_count} archived logs'
            }, 200
        except Exception as e:
            logger.error(f"Error cleaning up audit logs: {e}")
            return {'message': 'Internal server error'}, 500
