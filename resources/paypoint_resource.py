from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.paypoint_model import Paypoint
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for Paypoint-related operations
paypoint_ns = Namespace('paypoint', description='Paypoint operations')

# Define models for Swagger documentation
paypoint_model = paypoint_ns.model('Paypoint', {
    'id': fields.Integer(description='Paypoint ID'),
    'name': fields.String(required=True, description='Paypoint Name'),
    'location': fields.String(required=True, description='Paypoint Location')
})

# Helper function to check role permissions (allowing multiple roles)
def check_role_permission(current_user, required_roles):
    return current_user['role'].lower() in required_roles

@paypoint_ns.route('/')
class PaypointListResource(Resource):
    @paypoint_ns.doc(security='Bearer Auth')
    @jwt_required()
    @paypoint_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @paypoint_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @paypoint_ns.param('filter_by', 'Filter by Paypoint name', type='string')
    @paypoint_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of Paypoints."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        paypoint_query = Paypoint.query.filter_by(is_deleted=False)

        if filter_by:
            paypoint_query = paypoint_query.filter(Paypoint.name.ilike(f'%{filter_by}%'))

        # Validate sorting field
        valid_sort_fields = ['created_at', 'name', 'location']
        if sort_by not in valid_sort_fields:
            logger.error(f"Invalid sorting field: {sort_by}")
            return {'message': f'Invalid sorting field: {sort_by}'}, 400

        try:
            paypoints = paypoint_query.order_by(getattr(Paypoint, sort_by).desc()).paginate(page, per_page, error_out=False)
        except Exception as e:
            logger.error(f"Error during Paypoint sorting: {str(e)}")
            return {'message': 'Error retrieving Paypoints'}, 500

        if not paypoints.items:
            return {'message': 'No Paypoints found'}, 200

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='paypoint_list',
            resource_id=None,
            details="User accessed list of Paypoints"
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'paypoints': [paypoint.serialize() for paypoint in paypoints.items],
            'total': paypoints.total,
            'pages': paypoints.pages,
            'current_page': paypoints.page
        }, 200

    @paypoint_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Bad Request', 403: 'Unauthorized'})
    @jwt_required()
    @paypoint_ns.expect(paypoint_model, validate=True)
    def post(self):
        """Create a new Paypoint (admin only)."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if not check_role_permission(current_user, ['admin']):
            logger.warning(f"Unauthorized attempt by User ID {current_user['id']} to create Paypoint.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        if not data.get('name') or not data.get('location'):
            logger.error(f"Missing required fields in Paypoint creation by User ID {current_user['id']}.")
            return {'message': 'Missing required fields: name and location'}, 400

        new_paypoint = Paypoint(
            name=data['name'],
            location=data['location']
        )
        try:
            db.session.add(new_paypoint)
            db.session.commit()
        except Exception as e:
            logger.error(f"Database error during Paypoint creation by User ID {current_user['id']}: {str(e)}")
            return {'message': 'Failed to create Paypoint, please try again later.'}, 500

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='paypoint',
            resource_id=new_paypoint.id,
            details=f"User created a new Paypoint with ID {new_paypoint.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Paypoint ID {new_paypoint.id} created by User ID {current_user['id']}.")
        return new_paypoint.serialize(), 201

@paypoint_ns.route('/<int:paypoint_id>')
class PaypointResource(Resource):
    @paypoint_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Paypoint not found', 403: 'Unauthorized'})
    @jwt_required()
    def get(self, paypoint_id):
        """Retrieve a specific Paypoint by ID."""
        current_user = get_jwt_identity()
        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            logger.warning(f"Paypoint ID {paypoint_id} not found for User ID {current_user['id']}.")
            return {'message': 'Paypoint not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='paypoint',
            resource_id=paypoint_id,
            details=f"User accessed Paypoint with ID {paypoint_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return paypoint.serialize(), 200

    @paypoint_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Paypoint not found', 403: 'Unauthorized'})
    @jwt_required()
    @paypoint_ns.expect(paypoint_model, validate=True)
    def put(self, paypoint_id):
        """Update an existing Paypoint (admin only)."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if not check_role_permission(current_user, ['admin']):
            logger.warning(f"Unauthorized update attempt on Paypoint ID {paypoint_id} by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            logger.error(f"Paypoint ID {paypoint_id} not found for update by User ID {current_user['id']}.")
            return {'message': 'Paypoint not found'}, 404

        data = request.json
        paypoint.name = data.get('name', paypoint.name)
        paypoint.location = data.get('location', paypoint.location)
        paypoint.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='paypoint',
            resource_id=paypoint.id,
            details=f"User updated Paypoint with ID {paypoint.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Paypoint ID {paypoint.id} updated by User ID {current_user['id']}.")
        return paypoint.serialize(), 200

    @paypoint_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Paypoint not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, paypoint_id):
        """Soft-delete a Paypoint (admin only)."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if not check_role_permission(current_user, ['admin']):
            logger.warning(f"Unauthorized delete attempt on Paypoint ID {paypoint_id} by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            logger.error(f"Paypoint ID {paypoint_id} not found for deletion by User ID {current_user['id']}.")
            return {'message': 'Paypoint not found'}, 404

        paypoint.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='paypoint',
            resource_id=paypoint.id,
            details=f"User deleted Paypoint with ID {paypoint.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Paypoint ID {paypoint.id} soft-deleted by User ID {current_user['id']}.")
        return {'message': 'Paypoint deleted successfully'}, 200
