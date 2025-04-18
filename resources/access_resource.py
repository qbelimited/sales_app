from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import Role
from models.access_model import Access
from models.audit_model import AuditTrail, AuditAction
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create a namespace for access-related operations
access_ns = Namespace('access', description='Access control and management operations')

# Define models for Swagger documentation
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

permission_update_model = access_ns.model('PermissionUpdate', {
    'permissions': fields.List(
        fields.String,
        required=True,
        description='List of permissions to update'
    ),
    'value': fields.Boolean(
        required=True,
        description='Value to set for the permissions'
    )
})

# Utility function to check admin privileges
def is_admin():
    current_user = get_jwt_identity()
    if current_user and 'role' in current_user:
        return current_user.get('role').lower() == 'admin'
    return False

def log_audit_trail(action, resource_type, resource_id, details, user_id=None):
    """Helper function to log audit trail entries."""
    if user_id is None:
        user_id = get_jwt_identity()['id']

    audit = AuditTrail(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=get_client_ip(),
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(audit)
    db.session.commit()

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

        try:
            accesses = Access.get_active_access_rules()
            if not accesses:
                logger.warning("No access records found.")
                return {'message': 'No access records found'}, 404

            log_audit_trail(
                AuditAction.ACCESS,
                'role_access',
                None,
                f"User with ID {current_user['id']} retrieved access information for all roles"
            )

            return [access.serialize() for access in accesses], 200
        except Exception as e:
            logger.error(f"Error retrieving access records: {str(e)}")
            return {'message': 'Error retrieving access records'}, 500

    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(access_model, validate=True)
    @access_ns.response(201, 'Access record created or updated successfully')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Role not found')
    @jwt_required()
    def post(self):
        """Admin can create or update access rules for roles."""
        if not is_admin():
            logger.warning("Unauthorized attempt to modify access rules")
            return {'message': 'Unauthorized'}, 403

        try:
            data = request.json
            role = Role.query.filter_by(id=data['role_id']).first()

            if not role:
                logger.error(f"Role ID {data['role_id']} not found during access modification")
                return {'message': 'Role not found'}, 404

            access = Access.query.filter_by(role_id=role.id).first()
            if not access:
                access = Access(role_id=role.id)

            # Store old values for audit trail
            old_values = access.to_dict(include_metadata=False) if access else {}

            # Update permissions
            for permission in Access.get_all_permissions():
                if permission in data:
                    setattr(access, permission, data[permission])

            db.session.add(access)
            db.session.commit()

            # Log changes in audit trail
            changes = {
                k: {'old': old_values.get(k), 'new': getattr(access, k)}
                for k in Access.get_all_permissions()
                if k in data and old_values.get(k) != data[k]
            }

            log_audit_trail(
                AuditAction.UPDATE,
                'role_access',
                role.id,
                f"Admin updated access for role {role.name}. Changes: {changes}"
            )

            logger.info(f"Access rules updated for role ID {role.id}")
            return {'message': f'Access for role {role.name} updated successfully'}, 201
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Database error during access update: {str(e)}")
            return {'message': 'Error updating access rules'}, 500
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating access rules: {str(e)}")
            return {'message': 'Error updating access rules'}, 500

    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(role_id_model, validate=True)
    @access_ns.response(200, 'Access record deleted successfully')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Access not found')
    @jwt_required()
    def delete(self):
        """Admin can delete access rules for a specific role."""
        if not is_admin():
            logger.warning(f"Unauthorized attempt to delete access rules")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role = Role.query.filter_by(id=data['role_id']).first()

        if not role:
            logger.error(f"Role ID {data['role_id']} not found during access deletion")
            return {'message': 'Role not found'}, 404

        access = Access.query.filter_by(role_id=role.id).first()

        if not access:
            logger.warning(f"Access details not found for role ID {role.id}")
            return {'message': 'Access details not found'}, 404

        db.session.delete(access)

        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='DELETE',
            resource_type='role_access',
            resource_id=role.id,
            details=f"Admin deleted access for role {role.name}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Access for role ID {role.id} deleted by admin ID {get_jwt_identity()['id']}")
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
        role = Role.query.filter_by(id=role_id).first()

        if not role:
            logger.error(f"Role ID {role_id} not found during access retrieval")
            return {'message': 'Role not found'}, 404

        access = Access.query.filter_by(role_id=role.id).first()

        if not access:
            logger.warning(f"Access details not found for role ID {role.id}")
            return {'message': 'Access details not found'}, 404

        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='role_access',
            resource_id=role.id,
            details=f"User with ID {get_jwt_identity()['id']} retrieved access for role {role.name}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Access details retrieved for role ID {role.id}")
        return access.serialize(), 200

    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(access_model, validate=True)
    @access_ns.response(200, 'Access updated successfully')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Role not found')
    @jwt_required()
    def put(self, role_id):
        """Admin can update access rules for a specific role."""
        if not is_admin():
            logger.warning(f"Unauthorized attempt to update access rules for role ID {role_id}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role = Role.query.filter_by(id=role_id).first()

        if not role:
            logger.error(f"Role ID {role_id} not found during access update")
            return {'message': 'Role not found'}, 404

        access = Access.query.filter_by(role_id=role.id).first()

        if not access:
            access = Access(role_id=role.id)

        access.can_create = data.get('can_create', access.can_create)
        access.can_update = data.get('can_update', access.can_update)
        access.can_delete = data.get('can_delete', access.can_delete)
        access.can_view_logs = data.get('can_view_logs', access.can_view_logs)
        access.can_manage_users = data.get('can_manage_users', access.can_manage_users)
        access.can_view_audit_trail = data.get('can_view_audit_trail', access.can_view_audit_trail)

        db.session.add(access)

        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='UPDATE',
            resource_type='role_access',
            resource_id=role.id,
            details=f"Admin updated access for role {role.name}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Access rules updated for role ID {role_id}")
        return {'message': f'Access for role {role.name} updated successfully'}, 200

@access_ns.route('/permissions')
class AccessPermissionsResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """Get list of all available permission types."""
        return {'permissions': Access.get_all_permissions()}, 200

@access_ns.route('/check-permissions')
class CheckPermissionsResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(access_ns.model('PermissionCheck', {
        'permissions': fields.List(
            fields.String,
            required=True,
            description='List of permissions to check'
        ),
        'require_all': fields.Boolean(
            required=True,
            description='Whether all permissions are required'
        )
    }))
    @access_ns.response(200, 'Success')
    @access_ns.response(403, 'Unauthorized')
    @jwt_required()
    def post(self):
        """Check if the current user has the specified permissions."""
        try:
            data = request.json
            permissions = data['permissions']
            require_all = data['require_all']

            current_user = get_jwt_identity()
            access = Access.query.filter_by(role_id=current_user['role_id']).first()

            if not access:
                return {'message': 'Access rules not found'}, 404

            has_permission = (
                access.has_all_permissions(permissions)
                if require_all
                else access.has_any_permission(permissions)
            )

            return {
                'has_permission': has_permission,
                'permissions': permissions,
                'require_all': require_all
            }, 200
        except Exception as e:
            logger.error(f"Error checking permissions: {str(e)}")
            return {'message': 'Error checking permissions'}, 500

@access_ns.route('/role/<int:role_id>/permissions')
class RolePermissionsResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.response(200, 'Success')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Role not found')
    @jwt_required()
    def get(self, role_id):
        """Get all permissions for a specific role."""
        if not is_admin():
            return {'message': 'Unauthorized'}, 403

        access = Access.get_access_by_role(role_id)
        if not access:
            return {'message': 'Access rules not found for this role'}, 404

        return access.to_dict(), 200

    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(access_ns.model('PermissionUpdate', {
        'permissions': fields.List(
            fields.String,
            required=True,
            description='List of permissions to update'
        ),
        'value': fields.Boolean(
            required=True,
            description='Value to set for the permissions'
        )
    }))
    @access_ns.response(200, 'Success')
    @access_ns.response(403, 'Unauthorized')
    @access_ns.response(404, 'Role not found')
    @jwt_required()
    def put(self, role_id):
        """Update multiple permissions for a role at once."""
        if not is_admin():
            return {'message': 'Unauthorized'}, 403

        data = request.json
        permissions = data.get('permissions', [])
        value = data.get('value', False)

        if not permissions:
            return {'message': 'No permissions specified'}, 400

        access = Access.get_access_by_role(role_id)
        if not access:
            return {'message': 'Access rules not found for this role'}, 404

        for permission in permissions:
            if hasattr(access, permission):
                setattr(access, permission, value)

        db.session.add(access)

        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='UPDATE',
            resource_type='role_access',
            resource_id=role_id,
            details=(
                f"Admin updated permissions {permissions} "
                f"to {value} for role {role_id}"
            ),
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Permissions updated successfully'}, 200

@access_ns.route('/templates')
class AccessTemplatesResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.response(200, 'Success')
    @jwt_required()
    def get(self):
        """Get predefined permission templates for common roles."""
        templates = {
            'admin': {
                'can_create': True,
                'can_update': True,
                'can_delete': True,
                'can_view_logs': True,
                'can_manage_users': True,
                'can_view_audit_trail': True
            },
            'manager': {
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_view_logs': True,
                'can_manage_users': True,
                'can_view_audit_trail': True
            },
            'user': {
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_view_logs': False,
                'can_manage_users': False,
                'can_view_audit_trail': False
            }
        }
        return {'templates': templates}, 200

@access_ns.route('/bulk-update')
class BulkAccessUpdateResource(Resource):
    @access_ns.doc(security='Bearer Auth')
    @access_ns.expect(permission_update_model, validate=True)
    @access_ns.response(200, 'Permissions updated successfully')
    @access_ns.response(403, 'Unauthorized')
    @jwt_required()
    def post(self):
        """Update multiple permissions for a role at once."""
        if not is_admin():
            logger.warning("Unauthorized attempt to bulk update permissions")
            return {'message': 'Unauthorized'}, 403

        try:
            data = request.json
            permissions = data['permissions']
            value = data['value']

            # Validate permissions
            valid_permissions = Access.get_all_permissions()
            invalid_permissions = [
                p for p in permissions if p not in valid_permissions
            ]
            if invalid_permissions:
                return {
                    'message': 'Invalid permissions',
                    'invalid_permissions': invalid_permissions
                }, 400

            # Update permissions for all roles
            accesses = Access.query.all()
            for access in accesses:
                for permission in permissions:
                    setattr(access, permission, value)

            db.session.commit()

            log_audit_trail(
                AuditAction.UPDATE,
                'role_access',
                None,
                f"Bulk update of permissions: {permissions} to {value}"
            )

            return {'message': 'Permissions updated successfully'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in bulk permission update: {str(e)}")
            return {'message': 'Error updating permissions'}, 500
