from flask_restx import Namespace, Resource, fields
from flask import request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user_model import User
from models.audit_model import AuditTrail
from models.token_model import TokenBlacklist
from app import db
from werkzeug.security import check_password_hash

# Define a namespace for auth-related operations
auth_ns = Namespace('auth', description='Authentication operations')

# Define models for Swagger documentation
login_model = auth_ns.model('LoginResponse', {
    'message': fields.String(description='Login message'),
    'access_token': fields.String(description='JWT Access Token'),
    'user': fields.Nested(auth_ns.model('User', {
        'id': fields.Integer(description='User ID'),
        'email': fields.String(description='User email'),
        'name': fields.String(description='User name'),
        'role_id': fields.Integer(description='Role ID'),
    }))
})

logout_model = auth_ns.model('LogoutResponse', {
    'message': fields.String(description='Logout message')
})

# Authentication resource class for login
@auth_ns.route('/login')
class LoginResource(Resource):
    @auth_ns.expect(auth_ns.model('LoginCredentials', {
        'email': fields.String(required=True, description='User email'),
        'password': fields.String(required=True, description='User password')
    }), validate=True)
    @auth_ns.response(200, 'Success', model=login_model)
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Login user and return JWT access token."""
        data = request.json
        user = User.query.filter_by(email=data['email']).first()

        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, data['password']):
            return {'message': 'Invalid credentials'}, 401

        # Create JWT access token
        access_token = create_access_token(identity={'id': user.id, 'email': user.email, 'role': user.role.name})

        # Log login event to audit trail
        audit = AuditTrail(
            user_id=user.id,
            action='LOGIN',
            resource_type='user',
            resource_id=user.id,
            details=f"User {user.email} logged in"
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'message': 'Logged in successfully',
            'access_token': access_token,
            'user': user.serialize()
        }, 200

# Logout resource class
@auth_ns.route('/logout')
class LogoutResource(Resource):
    @auth_ns.doc(description='Logs the user out and invalidates the JWT token.')
    @auth_ns.response(200, 'Success', model=logout_model)
    @auth_ns.response(401, 'Unauthorized')
    @jwt_required()
    def post(self):
        """Logout user by blacklisting the JWT token."""
        current_user = get_jwt_identity()

        # Blacklist the JWT token (optional if using token blacklisting)
        jti = get_jwt()['jti']  # JWT ID (unique identifier for the token)
        token_blacklist = TokenBlacklist(jti=jti, user_id=current_user['id'], revoked=True)
        db.session.add(token_blacklist)

        # Log logout event to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='LOGOUT',
            resource_type='user',
            resource_id=current_user['id'],
            details=f"User {current_user['email']} logged out"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Logged out successfully'}, 200
