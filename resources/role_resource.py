from flask_restful import Resource
from flask import request, jsonify
from models.user_model import Role, User
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class RolesResource(Resource):
    @jwt_required()
    def get(self, role_id=None):
        """Get role or list of roles."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':  # Only admin can manage roles
            return {'message': 'Unauthorized'}, 403

        if role_id:
            role = Role.query.filter_by(id=role_id).first()
            if not role:
                return {'message': 'Role not found'}, 404
            return role.serialize(), 200
        else:
            roles = Role.query.all()
            return {'roles': [role.serialize() for role in roles]}, 200

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

    @jwt_required()
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
