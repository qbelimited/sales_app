from flask_restx import Namespace, Resource, fields
from flask import request
from models.user_model import Role
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define namespace for roles
role_ns = Namespace('roles', description='Role management operations')

# Define model for Swagger documentation
role_model = role_ns.model('Role', {
    'id': fields.Integer(description='Role ID'),
    'name': fields.String(required=True, description='Role Name'),
    'description': fields.String(description='Role Description'),
    'is_deleted': fields.Boolean(description='Soft delete flag')
})

@role_ns.route('/')
class RolesResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_list_with(role_model)
    def get(self):
        """Get list of roles."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':  # Only admin can manage roles
            logger.warning(f"Unauthorized access attempt by User ID {current_user['id']} to retrieve roles.")
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
            logger.warning(f"Unauthorized role creation attempt by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role_exists = Role.query.filter_by(name=data['name'], is_deleted=False).first()
        if role_exists:
            logger.error(f"Role creation failed: Role '{data['name']}' already exists.")
            return {'message': f"Role '{data['name']}' already exists."}, 400

        # Create new role
        new_role = Role(name=data['name'], description=data.get('description', ''))
        db.session.add(new_role)
        db.session.commit()

        # Log the role creation in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='role',
            resource_id=new_role.id,
            details=f"Admin created role with ID {new_role.id} and name {new_role.name}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Role '{new_role.name}' created by Admin (User ID {current_user['id']}).")
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
            logger.warning(f"Unauthorized update attempt by User ID {current_user['id']} on Role ID {role_id}.")
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            logger.error(f"Role ID {role_id} not found for update by User ID {current_user['id']}.")
            return {'message': 'Role not found'}, 404

        data = request.json
        role.name = data.get('name', role.name)
        role.description = data.get('description', role.description)
        role.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the role update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='role',
            resource_id=role.id,
            details=f"Admin updated role with ID {role.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Role ID {role.id} updated by Admin (User ID {current_user['id']}).")
        return role.serialize(), 200

    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, role_id):
        """Soft delete an existing role."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized deletion attempt by User ID {current_user['id']} on Role ID {role_id}.")
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id, is_deleted=False).first()
        if not role:
            logger.error(f"Role ID {role_id} not found for deletion by User ID {current_user['id']}.")
            return {'message': 'Role not found'}, 404

        role.is_deleted = True
        db.session.commit()

        # Log the role deletion in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='role',
            resource_id=role.id,
            details=f"Admin soft-deleted role with ID {role.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Role ID {role.id} soft-deleted by Admin (User ID {current_user['id']}).")
        return {'message': 'Role deleted successfully'}, 200
