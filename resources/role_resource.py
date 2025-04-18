from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import Role
from models.audit_model import AuditTrail
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip
import json
import logging

logger = logging.getLogger(__name__)

# Define namespace for roles
role_ns = Namespace('roles', description='Role management operations')

# Define models for Swagger documentation
role_model = role_ns.model('Role', {
    'id': fields.Integer(description='Role ID'),
    'name': fields.String(required=True, description='Role Name'),
    'description': fields.String(description='Role Description'),
    'is_deleted': fields.Boolean(description='Soft delete flag'),
    'parent_id': fields.Integer(description='Parent Role ID'),
    'status': fields.String(description='Role Status'),
    'validation_rules': fields.Raw(description='Role Validation Rules')
})

role_hierarchy_model = role_ns.model('RoleHierarchy', {
    'role': fields.Nested(role_model),
    'parent': fields.Nested(role_model),
    'children': fields.List(fields.Nested(role_model))
})

role_analytics_model = role_ns.model('RoleAnalytics', {
    'total_users': fields.Integer(description='Total users with this role'),
    'last_assigned': fields.DateTime(description='Last assignment timestamp'),
    'active_users': fields.Integer(description='Number of active users'),
    'inactive_users': fields.Integer(description='Number of inactive users')
})

@role_ns.route('/')
class RolesResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_list_with(role_model)
    def get(self):
        """Get list of roles."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(
                f"Unauthorized access attempt by User ID {current_user['id']}"
            )
            return {'message': 'Unauthorized'}, 403

        roles = Role.query.filter_by(is_deleted=False).all()
        logger.info(f"User ID {current_user['id']} retrieved roles list.")
        return roles, 200

    @role_ns.expect(role_model)
    @jwt_required()
    def post(self):
        """Create a new role."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(
                f"Unauthorized role creation attempt by User ID {current_user['id']}"
            )
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role_exists = Role.query.filter_by(
            name=data['name'],
            is_deleted=False
        ).first()
        if role_exists:
            logger.error(f"Role creation failed: Role '{data['name']}' exists")
            return {'message': f"Role '{data['name']}' already exists."}, 400

        # Create new role
        new_role = Role(
            name=data['name'],
            description=data.get('description', ''),
            parent_id=data.get('parent_id'),
            status=data.get('status', 'active'),
            validation_rules=json.dumps(data.get('validation_rules', {}))
        )
        db.session.add(new_role)
        db.session.commit()

        # Log the role creation in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='role',
            resource_id=new_role.id,
            details=f"Admin created role with ID {new_role.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(
            f"Role '{new_role.name}' created by Admin (User ID {current_user['id']})"
        )
        return new_role.serialize(), 201

@role_ns.route('/<int:role_id>')
class RoleByIdResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_with(role_model)
    def put(self, role_id):
        """Update an existing role."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(
                f"Unauthorized update attempt by User ID {current_user['id']}"
            )
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            logger.error(f"Role ID {role_id} not found")
            return {'message': 'Role not found'}, 404

        data = request.json
        role.name = data.get('name', role.name)
        role.description = data.get('description', role.description)
        role.parent_id = data.get('parent_id', role.parent_id)
        role.status = data.get('status', role.status)
        if 'validation_rules' in data:
            role.validation_rules = json.dumps(data['validation_rules'])

        db.session.commit()

        # Log the role update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='role',
            resource_id=role.id,
            details=f"Admin updated role with ID {role.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Role ID {role.id} updated by Admin")
        return role.serialize(), 200

    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, role_id):
        """Soft delete an existing role."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(
                f"Unauthorized deletion attempt by User ID {current_user['id']}"
            )
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            logger.error(f"Role ID {role_id} not found")
            return {'message': 'Role not found'}, 404

        try:
            # Soft delete the role
            role.is_deleted = True
            db.session.commit()

            # Log the role deletion in the audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='DELETE',
                resource_type='role',
                resource_id=role.id,
                details=f"Admin soft-deleted role with ID {role.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Role ID {role.id} soft-deleted by Admin")
            return {'message': 'Role deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting role ID {role_id}: {str(e)}")
            return {'message': 'Failed to delete role'}, 500

@role_ns.route('/hierarchy')
class RoleHierarchyResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_with(role_hierarchy_model)
    def get(self):
        """Get the complete role hierarchy."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        role_id = request.args.get('role_id', type=int)
        hierarchy = Role.get_role_hierarchy(role_id)
        if not hierarchy:
            return {'message': 'Role hierarchy not found'}, 404

        return hierarchy, 200

@role_ns.route('/<int:role_id>/analytics')
class RoleAnalyticsResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_with(role_analytics_model)
    def get(self, role_id):
        """Get analytics for a specific role."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            return {'message': 'Role not found'}, 404

        return role.get_usage_analytics(), 200

@role_ns.route('/<int:role_id>/validate')
class RoleValidationResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    def post(self, role_id):
        """Validate user data against role validation rules."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            return {'message': 'Role not found'}, 404

        data = request.json
        is_valid, error = role.validate_rules(data)
        if not is_valid:
            return {'message': error}, 400

        return {'message': 'Validation successful'}, 200

@role_ns.route('/<int:role_id>/status')
class RoleStatusResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    def put(self, role_id):
        """Update role status."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            return {'message': 'Role not found'}, 404

        data = request.json
        new_status = data.get('status')
        if not new_status:
            return {'message': 'Status is required'}, 400

        try:
            role.update_status(new_status)
            return {'message': 'Role status updated successfully'}, 200
        except ValueError as e:
            return {'message': str(e)}, 400
