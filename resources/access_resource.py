from flask_restful import Resource
from flask import request, jsonify
from models.user_model import Role, User
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

class AccessResource(Resource):
    @jwt_required()
    def get(self):
        """Get access details for the current user."""
        current_user = get_jwt_identity()
        role = Role.query.filter_by(id=current_user['role_id']).first()

        if not role:
            return {'message': 'Role not found'}, 404

        access_details = self.get_access_for_role(role.name)

        return {
            'role': role.name,
            'access': access_details
        }, 200

    @staticmethod
    def get_access_for_role(role_name):
        """Define access control rules based on roles."""
        access_control = {
            'admin': {
                'can_create': True,
                'can_update': True,
                'can_delete': True,
                'can_view_logs': True,
                'can_manage_users': True,
                'can_view_audit_trail': True,
            },
            'manager': {
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_view_logs': False,
                'can_manage_users': False,
                'can_view_audit_trail': True,
            },
            'sales_executive': {
                'can_create': True,
                'can_update': True,
                'can_delete': False,
                'can_view_logs': False,
                'can_manage_users': False,
                'can_view_audit_trail': False,
            },
            'back_office': {
                'can_create': False,
                'can_update': False,
                'can_delete': False,
                'can_view_logs': False,
                'can_manage_users': False,
                'can_view_audit_trail': True,
            }
        }
        return access_control.get(role_name, {})

    @jwt_required()
    def post(self):
        """Admin can update access rules for roles."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        role = Role.query.filter_by(id=data['role_id']).first()
        if not role:
            return {'message': 'Role not found'}, 404

        # Log the access update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='role_access',
            resource_id=role.id,
            details=f"Admin updated access for role {role.name}"
        )
        db.session.add(audit)
        db.session.commit()

        # This is a placeholder for future access updates if you want to store it in the database
        return {'message': f'Access for role {role.name} updated successfully'}, 200
