from flask_restx import Namespace, Resource, fields
from flask import request
from models.audit_model import AuditTrail, AuditAction
from app import logger, db
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
from datetime import datetime

# Define namespace for audit trails
audit_ns = Namespace('audit_trail', description='Audit trail operations')

# Define model for Swagger documentation
audit_model = audit_ns.model('AuditTrail', {
    'id': fields.Integer(description='Audit ID'),
    'user_id': fields.Integer(required=True, description='User ID who performed the action'),
    'action': fields.String(required=True, description='Action performed (CREATE, UPDATE, DELETE, etc.)'),
    'resource_type': fields.String(required=True, description='The type of resource affected (e.g., "role", "user")'),
    'resource_id': fields.Integer(description='The ID of the resource affected'),
    'old_value': fields.String(description='The previous value before the action'),
    'new_value': fields.String(description='The new value after the action'),
    'timestamp': fields.DateTime(description='When the action occurred'),
    'details': fields.String(description='Additional details about the action'),
    'ip_address': fields.String(description='IP address of the user'),
    'user_agent': fields.String(description='User agent of the user')
})

@audit_ns.route('/')
class AuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @audit_ns.marshal_list_with(audit_model)
    @jwt_required()
    def get(self):
        """Get the audit trail logs."""
        current_user = get_jwt_identity()

        # Only allow admins to view audit logs
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt to view audit trail by user ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        # Optional query parameters to filter the logs
        user_id = request.args.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        resource_type = request.args.get('resource_type')
        action = request.args.get('action')

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
                logger.error(f"Invalid start date format for filtering: {start_date}.")
                return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(AuditTrail.timestamp <= end_dt)
            except ValueError:
                logger.error(f"Invalid end date format for filtering: {end_date}.")
                return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        # Filter by resource type (case-insensitive, partial match)
        if resource_type:
            query = query.filter(AuditTrail.resource_type.ilike(f"%{resource_type}%"))

        # Filter by action (case-insensitive, partial match)
        if action:
            if action.upper() in AuditAction.__members__:
                query = query.filter(AuditTrail.action.ilike(f"%{action.upper()}%"))
            else:
                logger.error(f"Invalid action type provided: {action}.")
                return {'message': f"Invalid action type. Valid types are: {', '.join(AuditAction.__members__.keys())}"}, 400

        audit_trails = query.order_by(AuditTrail.timestamp.desc()).all()

        logger.info(f"User ID {current_user['id']} retrieved audit trail logs.")
        return audit_trails, 200

@audit_ns.route('/<int:audit_id>')
class SingleAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @audit_ns.response(200, 'Success', audit_model)
    @audit_ns.response(404, 'Audit log not found')
    @jwt_required()
    def get(self, audit_id):
        """Retrieve a specific audit log by its ID."""
        current_user = get_jwt_identity()

        # Only allow admins to view audit logs
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt to view audit log ID {audit_id} by user ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        audit_log = AuditTrail.query.filter_by(id=audit_id).first()

        if not audit_log:
            logger.error(f"Audit log ID {audit_id} not found.")
            return {'message': 'Audit log not found'}, 404

        logger.info(f"Audit log ID {audit_id} retrieved by user ID {current_user['id']}.")
        return audit_log.serialize(), 200

@audit_ns.route('/filter')
class FilteredAuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @audit_ns.marshal_list_with(audit_model)
    def post(self):
        """Filter the audit logs by resource type, action, or date range."""
        current_user = get_jwt_identity()

        # Only admins can filter audit logs
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt to filter audit logs by user ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        data = request.get_json()

        resource_type = data.get('resource_type')
        action = data.get('action')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        query = AuditTrail.query

        # Apply filters if provided
        if resource_type:
            query = query.filter(AuditTrail.resource_type.ilike(f"%{resource_type}%"))

        if action:
            if action.upper() in AuditAction.__members__:
                query = query.filter(AuditTrail.action.ilike(f"%{action.upper()}%"))
            else:
                logger.error(f"Invalid action type provided: {action}.")
                return {'message': f"Invalid action type. Valid types are: {', '.join(AuditAction.__members__.keys())}"}, 400

        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(AuditTrail.timestamp >= start_dt)
            except ValueError:
                logger.error(f"Invalid start date format for filtering: {start_date}.")
                return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(AuditTrail.timestamp <= end_dt)
            except ValueError:
                logger.error(f"Invalid end date format for filtering: {end_date}.")
                return {'message': 'Invalid date format. Use YYYY-MM-DD'}, 400

        filtered_audits = query.order_by(AuditTrail.timestamp.desc()).all()

        # Log this action with IP and user agent
        new_audit_entry = AuditTrail(
            user_id=current_user['id'],
            action='FILTER',
            resource_type='audit_trail',
            timestamp=datetime.utcnow(),
            details=f"Filtered audit logs for resource type: {resource_type}, action: {action}, dates: {start_date} - {end_date}.",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(new_audit_entry)
        db.session.commit()

        logger.info(f"User ID {current_user['id']} filtered audit logs with IP {ip_address} and User Agent {user_agent}.")
        return filtered_audits, 200
