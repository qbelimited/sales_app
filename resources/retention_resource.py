from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.retention_model import RetentionPolicy
from models.audit_model import AuditTrail
from app import db, logger

# Define a namespace for retention policy operations
retention_ns = Namespace('retention', description='Retention Policy operations')

# Define models for Swagger documentation
retention_policy_model = retention_ns.model('RetentionPolicy', {
    'id': fields.Integer(description='Policy ID'),
    'retention_days': fields.Integer(required=True, description='Number of days for data retention'),
    'updated_at': fields.String(description='Last updated timestamp')
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
            # Fetch the current policy or create a default one if it doesn't exist
            policy = RetentionPolicy.get_current_policy()

            # Log access to the audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='retention_policy',
                resource_id=policy.id,
                details="User accessed the current retention policy"
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"User {current_user['id']} accessed retention policy with ID {policy.id}")
            return policy.serialize(), 200
        except Exception as e:
            logger.error(f"Error fetching retention policy for User {current_user['id']}: {str(e)}")
            return {'message': 'Error fetching retention policy'}, 500

    @retention_ns.expect(retention_policy_model, validate=True)
    @retention_ns.doc(security='Bearer Auth', responses={200: 'Updated', 400: 'Invalid Input'})
    @jwt_required()
    def put(self):
        """Update the retention policy."""
        current_user = get_jwt_identity()
        data = request.json

        try:
            # Fetch the current policy
            policy = RetentionPolicy.get_current_policy()

            # Update the retention days
            retention_days = data.get('retention_days')
            if retention_days:
                policy.retention_days = retention_days
                db.session.commit()

                # Log the update to audit trail
                audit = AuditTrail(
                    user_id=current_user['id'],
                    action='UPDATE',
                    resource_type='retention_policy',
                    resource_id=policy.id,
                    details=f"User updated retention policy to {retention_days} days"
                )
                db.session.add(audit)
                db.session.commit()

                logger.info(f"User {current_user['id']} updated retention policy to {retention_days} days")
                return policy.serialize(), 200
            else:
                logger.warning(f"User {current_user['id']} provided invalid retention days")
                return {'message': 'Invalid retention days'}, 400
        except ValueError as e:
            logger.error(f"Validation error: {str(e)} for User {current_user['id']}")
            return {'message': str(e)}, 400
        except Exception as e:
            logger.error(f"Error updating retention policy for User {current_user['id']}: {str(e)}")
            return {'message': 'Error updating retention policy'}, 500
