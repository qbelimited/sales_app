from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.audit_model import AuditTrail
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

# Define a namespace for audit-related operations
audit_ns = Namespace('audit', description='Audit trail operations')

# Define the model for the audit trail in Swagger documentation
audit_model = audit_ns.model('AuditTrail', {
    'id': fields.Integer(description='Audit ID'),
    'user_id': fields.Integer(description='User ID'),
    'action': fields.String(required=True, description='Action performed'),
    'resource_type': fields.String(required=True, description='Type of resource'),
    'resource_id': fields.Integer(description='Resource ID'),
    'details': fields.String(description='Details of the action'),
    'timestamp': fields.DateTime(description='Timestamp of the action')
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'back_office': ['admin', 'manager', 'back_office'],
        'sales_manager': ['admin', 'manager', 'sales_manager']
    }
    return current_user['role'] in roles.get(required_role, [])

@audit_ns.route('/')
class AuditTrailResource(Resource):
    @audit_ns.doc(security='Bearer Auth')
    @jwt_required()
    @audit_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @audit_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @audit_ns.param('filter_by', 'Filter by action details', type='string')
    @audit_ns.param('sort_by', 'Sort by field (e.g., timestamp, action)', type='string', default='timestamp')
    def get(self):
        """Retrieve paginated audit trail logs (admin only)."""
        current_user = get_jwt_identity()
        if not check_role_permission(current_user, 'admin'):
            return {'message': 'Unauthorized'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'timestamp')

        audit_query = AuditTrail.query

        if filter_by:
            audit_query = audit_query.filter(AuditTrail.details.ilike(f'%{filter_by}%'))

        audits = audit_query.order_by(sort_by).paginate(page, per_page, error_out=False)

        return {
            'audits': [audit.serialize() for audit in audits.items],
            'total': audits.total,
            'pages': audits.pages,
            'current_page': audits.page
        }, 200
