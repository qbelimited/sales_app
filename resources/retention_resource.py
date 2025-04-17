from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.retention_model import RetentionPolicy, DataType, DataImportance
from models.audit_model import AuditTrail
from app import db, logger
from utils import get_client_ip

# Define a namespace for retention policy operations
retention_ns = Namespace(
    'retention',
    description='Retention Policy operations'
)

# Define models for Swagger documentation
retention_policy_model = retention_ns.model('RetentionPolicy', {
    'id': fields.Integer(description='Policy ID'),
    'data_type': fields.String(
        required=True,
        description='Type of data (sales, audit, reports, etc.)'
    ),
    'importance': fields.String(
        required=True,
        description='Importance level (critical, high, medium, low)'
    ),
    'retention_days': fields.Integer(
        required=True,
        description='Number of days for data retention'
    ),
    'archive_before_delete': fields.Boolean(
        description='Whether to archive before deletion'
    ),
    'max_retention_days': fields.Integer(
        description='Maximum allowed retention days'
    ),
    'notification_days': fields.Integer(
        description='Days before expiration to notify'
    ),
    'created_at': fields.String(description='Creation timestamp'),
    'updated_at': fields.String(description='Last updated timestamp')
})

data_volume_model = retention_ns.model('DataVolume', {
    'total_records': fields.Integer(description='Total number of records'),
    'expiring_records': fields.Integer(
        description='Number of records approaching expiration'
    ),
    'retention_days': fields.Integer(description='Current retention period'),
    'data_type': fields.String(description='Type of data')
})

@retention_ns.route('/')
class RetentionPolicyResource(Resource):
    @retention_ns.doc(security='Bearer Auth')
    @retention_ns.marshal_with(retention_policy_model)
    @jwt_required()
    def get(self):
        """Retrieve the current retention policy or create a default one."""
        current_user = get_jwt_identity()

        try:
            # Fetch the current retention policy or create a default one
            policy = RetentionPolicy.get_current_policy()

            # Log access to the audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='retention_policy',
                resource_id=policy.id,
                details="User accessed the retention policy",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(
                f"User {current_user['id']} accessed retention policy with ID {policy.id}"
            )
            return policy.serialize(), 200
        except Exception as e:
            logger.error(
                f"Error fetching retention policy for User {current_user['id']}: {str(e)}"
            )
            return {'message': 'Error fetching retention policy'}, 500

    @retention_ns.expect(retention_policy_model, validate=True)
    @retention_ns.doc(
        security='Bearer Auth',
        responses={200: 'Updated', 400: 'Invalid Input'}
    )
    @jwt_required()
    def put(self):
        """Update the retention policy."""
        current_user = get_jwt_identity()
        data = request.json

        try:
            # Update the retention policy with all provided fields
            policy = RetentionPolicy.update_policy(
                data_type=data.get('data_type'),
                retention_days=data.get('retention_days'),
                importance=data.get('importance'),
                archive_before_delete=data.get('archive_before_delete'),
                max_retention_days=data.get('max_retention_days'),
                notification_days=data.get('notification_days')
            )

            # Log the update to the audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='retention_policy',
                resource_id=policy.id,
                details=f"User updated retention policy: {data}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(
                f"User {current_user['id']} updated retention policy with ID {policy.id}"
            )
            return policy.serialize(), 200
        except ValueError as e:
            logger.error(
                f"Validation error: {str(e)} for User {current_user['id']}"
            )
            return {'message': str(e)}, 400
        except Exception as e:
            logger.error(
                f"Error updating retention policy for User {current_user['id']}: {str(e)}"
            )
            return {'message': 'Error updating retention policy'}, 500

@retention_ns.route('/volume/<string:data_type>')
class RetentionVolumeResource(Resource):
    @retention_ns.doc(security='Bearer Auth')
    @retention_ns.marshal_with(data_volume_model)
    @jwt_required()
    def get(self, data_type):
        """Get data volume statistics for a specific data type."""
        current_user = get_jwt_identity()

        try:
            volume_stats = RetentionPolicy.get_data_volume(data_type)

            # Log access to the audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='retention_volume',
                details=f"User accessed volume statistics for {data_type}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return volume_stats, 200
        except Exception as e:
            logger.error(
                f"Error fetching volume statistics for User {current_user['id']}: {str(e)}"
            )
            return {'message': 'Error fetching volume statistics'}, 500

@retention_ns.route('/types')
class RetentionTypesResource(Resource):
    @retention_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Get all available data types for retention policies."""
        current_user = get_jwt_identity()

        try:
            data_types = [
                {'value': t.value, 'label': t.value.capitalize()}
                for t in DataType
            ]
            importance_levels = [
                {'value': i.value, 'label': i.value.capitalize()}
                for i in DataImportance
            ]

            return {
                'data_types': data_types,
                'importance_levels': importance_levels
            }, 200
        except Exception as e:
            logger.error(
                f"Error fetching retention types for User {current_user['id']}: {str(e)}"
            )
            return {'message': 'Error fetching retention types'}, 500
