from flask_restful import Resource
from flask import request, jsonify
from models.user_model import User
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class UserResource(Resource):
    @jwt_required()
    def get(self, user_id=None):
        current_user = get_jwt_identity()
        if user_id:
            user = User.query.filter_by(id=user_id, is_deleted=False).first()
            if not user:
                return {'message': 'User not found'}, 404

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='user',
                resource_id=user_id,
                details=f"User accessed details of User with ID {user_id}"
            )
            db.session.add(audit)
            db.session.commit()

            return user.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            user_query = User.query.filter_by(is_deleted=False)

            if filter_by:
                user_query = user_query.filter(User.name.ilike(f'%{filter_by}%'))

            users = user_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='user_list',
                resource_id=None,
                details=f"User accessed list of Users"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'users': [user.serialize() for user in users.items],
                'total': users.total,
                'pages': users.pages,
                'current_page': users.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data = request.json

        new_user = User(
            email=data['email'],
            name=data['name'],
            role_id=data['role_id'],
            microsoft_id=data['microsoft_id']
        )
        db.session.add(new_user)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='user',
            resource_id=new_user.id,
            details=f"User created a new User with ID {new_user.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_user.serialize(), 201

    @jwt_required()
    def put(self, user_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return {'message': 'User not found'}, 404

        data = request.json
        user.email = data.get('email', user.email)
        user.name = data.get('name', user.name)
        user.role_id = data.get('role_id', user.role_id)
        user.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='user',
            resource_id=user.id,
            details=f"User updated User with ID {user.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return user.serialize(), 200

    @jwt_required()
    def delete(self, user_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return {'message': 'User not found'}, 404

        user.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='user',
            resource_id=user.id,
            details=f"User deleted User with ID {user.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'User deleted successfully'}, 200
