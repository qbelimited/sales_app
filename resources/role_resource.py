from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.user_model import Role
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define namespace for roles
role_ns = Namespace('roles', description='Role management operations')

# Define model for Swagger documentation
role_model = role_ns.model('Role', {
    'id': fields.Integer(description='Role ID'),
    'name': fields.String(required=True, description='Role Name'),
    'description': fields.String(description='Role Description')
})

@role_ns.route('/')
class RolesResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_list_with(role_model)
    def get(self):
        """Get role or list of roles."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':  # Only admin can manage roles
            return {'message': 'Unauthorized'}, 403

        roles = Role.query.all()
        return roles, 200

    @role_ns.expect(role_model)
    @jwt_required()
    def post(self):
        """Create a new role."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_role = Role(name=data['name'], description=data['description'])
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

        return new_role.serialize(), 201

@role_ns.route('/<int:role_id>')
class RoleByIdResource(Resource):
    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    @role_ns.marshal_with(role_model)
    def put(self, role_id):
        """Update an existing role."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id).first()
        if not role:
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

        return role.serialize(), 200

    @role_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, role_id):
        """Delete an existing role."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        role = Role.query.filter_by(id=role_id).first()
        if not role:
            return {'message': 'Role not found'}, 404

        db.session.delete(role)
        db.session.commit()

        # Log the role deletion in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='role',
            resource_id=role.id,
            details=f"Admin deleted role with ID {role.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Role deleted successfully'}, 200
