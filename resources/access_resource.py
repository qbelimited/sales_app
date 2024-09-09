from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import Role
from models.access_model import Access
from models.audit_model import AuditTrail
from app import db, logger  # Import logger from app.py
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create a namespace for access-related operations
access_ns = Namespace('access', description='Access control and management operations')

# Define the models for Swagger documentation
access_model = access_ns.model('Access', {
    'role_id': fields.Integer(required=True, description='Role ID'),
    'can_create': fields.Boolean(description='Permission to create'),
    'can_update': fields.Boolean(description='Permission to update'),
    'can_delete': fields.Boolean(description='Permission to delete'),
    'can_view_logs': fields.Boolean(description='Permission to view logs'),
    'can_manage_users': fields.Boolean(description='Permission to manage users'),
    'can_view_audit_trail': fields.Boolean(description='Permission to view audit trail')
})

role_id_model = access_ns.model('RoleID', {
    'role_id': fields.Integer(required=True, description='Role ID')
})


@access_ns.route('/')
class AccessResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.response(200, 'Success', [access_model])
    @access_ns.response(404, 'Access not found')
    @jwt_required()
    def get(self):
        """Get access details for all roles."""
        current_user = get_jwt_identity()
        logger.info(f"User {current_user['id']} requested all access records.")

        # Fetch all access records
        accesses = Access.query.all()

        if not accesses:
            logger.warning("No access records found.")
            return {'message': 'No access records found'}, 404

        return [access.serialize() for access in accesses], 200

    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(access_model, validate=True)
    @access_ns.response(201, 'Access record created or updated successfully')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Role not found')
    @jwt_required()
    def post(self):
        """Admin can create or update access rules for roles."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to modify access rules by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role = Role.query.filter_by(id=data['role_id']).first()

        if not role:
            logger.error(f"Role ID {data['role_id']} not found during access modification")
            return {'message': 'Role not found'}, 404

        # Create or update the access object for the role
        access = Access.query.filter_by(role_id=role.id).first()
        if not access:
            access = Access(role_id=role.id)

        # Update access permissions based on the request data
        access.can_create = data.get('can_create', access.can_create)
        access.can_update = data.get('can_update', access.can_update)
        access.can_delete = data.get('can_delete', access.can_delete)
        access.can_view_logs = data.get('can_view_logs', access.can_view_logs)
        access.can_manage_users = data.get('can_manage_users', access.can_manage_users)
        access.can_view_audit_trail = data.get('can_view_audit_trail', access.can_view_audit_trail)

        db.session.add(access)

        # Log the access creation or update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='role_access',
            resource_id=role.id,
            details=f"Admin updated access for role {role.name}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Access rules updated for role ID {role.id} by admin ID {current_user['id']}")
        return {'message': f'Access for role {role.name} updated successfully'}, 201

    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(role_id_model, validate=True)
    @access_ns.response(200, 'Access record deleted successfully')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Access not found')
    @jwt_required()
    def delete(self):
        """Admin can delete access rules for a specific role."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to delete access rules by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role = Role.query.filter_by(id=data['role_id']).first()

        if not role:
            logger.error(f"Role ID {data['role_id']} not found during access deletion")
            return {'message': 'Role not found'}, 404

        # Find and delete the access object
        access = Access.query.filter_by(role_id=role.id).first()

        if not access:
            logger.warning(f"Access details not found for role ID {role.id}")
            return {'message': 'Access details not found'}, 404

        db.session.delete(access)

        # Log the deletion in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='role_access',
            resource_id=role.id,
            details=f"Admin deleted access for role {role.name}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Access for role ID {role.id} deleted by admin ID {current_user['id']}")
        return {'message': f'Access for role {role.name} deleted successfully'}, 200


@access_ns.route('/<int:role_id>')
class SingleAccessResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.response(200, 'Success', access_model)
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Access not found')
    @jwt_required()
    def get(self, role_id):
        """Get access rules for a specific role by role ID."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to view access rules for role ID {role_id} by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id).first()

        if not role:
            logger.error(f"Role ID {role_id} not found during access retrieval")
            return {'message': 'Role not found'}, 404

        access = Access.query.filter_by(role_id=role.id).first()

        if not access:
            logger.warning(f"Access details not found for role ID {role.id}")
            return {'message': 'Access details not found'}, 404

        logger.info(f"Access details retrieved for role ID {role.id}")
        return access.serialize(), 200
