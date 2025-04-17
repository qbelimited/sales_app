from flask_restx import Namespace, Resource, fields
from flask import request
from models.paypoint_model import Paypoint
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip

# Define a namespace for Paypoint-related operations
paypoint_ns = Namespace('paypoint', description='Paypoint operations')

# Define models for Swagger documentation
paypoint_model = paypoint_ns.model('Paypoint', {
    'id': fields.Integer(description='Paypoint ID'),
    'name': fields.String(required=True, description='Paypoint Name'),
    'location': fields.String(description='Paypoint Location'),
    'contact_person': fields.String(description='Contact Person'),
    'contact_phone': fields.String(description='Contact Phone'),
    'contact_email': fields.String(description='Contact Email'),
    'operating_hours': fields.String(description='Operating Hours'),
    'status': fields.String(description='Status (active/inactive/suspended)'),
    'is_deleted': fields.Boolean(description='Whether the paypoint is deleted'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

# Helper function to check role permissions
def check_role_permission(current_user, required_roles):
    return current_user['role'].lower() in required_roles

@paypoint_ns.route('/')
class PaypointListResource(Resource):
    @paypoint_ns.doc(security='Bearer Auth')
    @jwt_required()
    @paypoint_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @paypoint_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @paypoint_ns.param('filter_by', 'Filter by Paypoint name', type='string')
    @paypoint_ns.param('status', 'Filter by status', type='string')
    @paypoint_ns.param('sort_by', 'Sort by field', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of Paypoints."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        status = request.args.get('status', None)
        sort_by = request.args.get('sort_by', 'created_at')

        # Validate sorting field
        valid_sort_fields = ['created_at', 'name', 'location', 'status']
        if sort_by not in valid_sort_fields:
            logger.error(f"Invalid sorting field: {sort_by}")
            return {'message': f'Invalid sorting field: {sort_by}'}, 400

        try:
            paypoint_query = Paypoint.query.filter_by(is_deleted=False)

            if filter_by:
                paypoint_query = paypoint_query.filter(Paypoint.name.ilike(f'%{filter_by}%'))

            if status:
                paypoint_query = paypoint_query.filter_by(status=status)

            paypoints = paypoint_query.order_by(getattr(Paypoint, sort_by).desc()).paginate(page=page, per_page=per_page, error_out=False)

            if not paypoints.items:
                return {'message': 'No Paypoints found'}, 200

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='paypoint_list',
                details="User accessed list of Paypoints",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'paypoints': [paypoint.serialize() for paypoint in paypoints.items],
                'total': paypoints.total,
                'pages': paypoints.pages,
                'current_page': paypoints.page
            }, 200

        except Exception as e:
            logger.error(f"Error retrieving Paypoints: {str(e)}")
            return {'message': 'Error retrieving Paypoints'}, 500

    @paypoint_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Bad Request', 403: 'Unauthorized'})
    @jwt_required()
    @paypoint_ns.expect(paypoint_model, validate=True)
    def post(self):
        """Create a new Paypoint (admin only)."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if not check_role_permission(current_user, ['admin', 'manager']):
            logger.warning(f"Unauthorized attempt by User ID {current_user['id']} to create Paypoint.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        if not data.get('name'):
            logger.error(f"Missing required fields in Paypoint creation by User ID {current_user['id']}.")
            return {'message': 'Missing required field: name'}, 400

        try:
            new_paypoint = Paypoint(
                name=data['name'],
                location=data.get('location', ''),
                contact_person=data.get('contact_person', ''),
                contact_phone=data.get('contact_phone', ''),
                contact_email=data.get('contact_email', ''),
                operating_hours=data.get('operating_hours', ''),
                status=data.get('status', 'active')
            )
            db.session.add(new_paypoint)
            db.session.commit()

            # Log the creation to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='paypoint',
                resource_id=new_paypoint.id,
                details=f"User created a new Paypoint with ID {new_paypoint.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Paypoint ID {new_paypoint.id} created by User ID {current_user['id']}.")
            return new_paypoint.serialize(), 201

        except Exception as e:
            logger.error(f"Database error during Paypoint creation by User ID {current_user['id']}: {str(e)}")
            return {'message': 'Failed to create Paypoint, please try again later.'}, 500

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
            details=f"User accessed Paypoint with ID {paypoint_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return paypoint.serialize(), 200

    @paypoint_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Paypoint not found', 403: 'Unauthorized'})
    @jwt_required()
    @paypoint_ns.expect(paypoint_model, validate=True)
    def put(self, paypoint_id):
        """Update an existing Paypoint (admin and manager only)."""
        current_user = get_jwt_identity()

        # Check if the user has admin privileges
        if not check_role_permission(current_user, ['admin', 'manager']):
            logger.warning(f"Unauthorized update attempt on Paypoint ID {paypoint_id} by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            logger.error(f"Paypoint ID {paypoint_id} not found for update by User ID {current_user['id']}.")
            return {'message': 'Paypoint not found'}, 404

        data = request.json
        try:
            paypoint.name = data.get('name', paypoint.name)
            paypoint.location = data.get('location', paypoint.location)
            paypoint.contact_person = data.get('contact_person', paypoint.contact_person)
            paypoint.contact_phone = data.get('contact_phone', paypoint.contact_phone)
            paypoint.contact_email = data.get('contact_email', paypoint.contact_email)
            paypoint.operating_hours = data.get('operating_hours', paypoint.operating_hours)
            paypoint.status = data.get('status', paypoint.status)
            paypoint.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the update to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='paypoint',
                resource_id=paypoint.id,
                details=f"User updated Paypoint with ID {paypoint.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Paypoint ID {paypoint.id} updated by User ID {current_user['id']}.")
            return paypoint.serialize(), 200

        except Exception as e:
            logger.error(f"Error updating Paypoint ID {paypoint_id}: {str(e)}")
            return {'message': 'Error updating Paypoint'}, 500

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

        try:
            paypoint.is_deleted = True
            paypoint.status = 'inactive'
            paypoint.updated_at = datetime.utcnow()
            db.session.commit()

            # Log the deletion to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='DELETE',
                resource_type='paypoint',
                resource_id=paypoint.id,
                details=f"User deleted Paypoint with ID {paypoint.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Paypoint ID {paypoint.id} soft-deleted by User ID {current_user['id']}.")
            return {'message': 'Paypoint deleted successfully'}, 200

        except Exception as e:
            logger.error(f"Error deleting Paypoint ID {paypoint_id}: {str(e)}")
            return {'message': 'Error deleting Paypoint'}, 500

@paypoint_ns.route('/<int:paypoint_id>/status')
class PaypointStatusResource(Resource):
    @paypoint_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Paypoint not found', 403: 'Unauthorized'})
    @jwt_required()
    def put(self, paypoint_id):
        """Update Paypoint status (admin and manager only)."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user, ['admin', 'manager']):
            logger.warning(f"Unauthorized status update attempt on Paypoint ID {paypoint_id} by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            logger.error(f"Paypoint ID {paypoint_id} not found for status update by User ID {current_user['id']}.")
            return {'message': 'Paypoint not found'}, 404

        data = request.json
        new_status = data.get('status')

        if not new_status:
            return {'message': 'Status is required'}, 400

        try:
            if new_status == 'suspended':
                paypoint.suspend()
            elif new_status == 'active':
                paypoint.activate()
            else:
                return {'message': 'Invalid status'}, 400

            # Log the status update to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='paypoint_status',
                resource_id=paypoint.id,
                details=f"User updated Paypoint status to {new_status}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"Paypoint ID {paypoint.id} status updated to {new_status} by User ID {current_user['id']}.")
            return paypoint.serialize(), 200

        except Exception as e:
            logger.error(f"Error updating Paypoint ID {paypoint_id} status: {str(e)}")
            return {'message': 'Error updating Paypoint status'}, 500

@paypoint_ns.route('/<int:paypoint_id>/stats')
class PaypointStatsResource(Resource):
    @paypoint_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Paypoint not found'})
    @jwt_required()
    def get(self, paypoint_id):
        """Get Paypoint statistics."""
        current_user = get_jwt_identity()
        paypoint = Paypoint.query.filter_by(id=paypoint_id, is_deleted=False).first()
        if not paypoint:
            logger.warning(f"Paypoint ID {paypoint_id} not found for stats by User ID {current_user['id']}.")
            return {'message': 'Paypoint not found'}, 404

        try:
            sales_count = Paypoint.get_sales_count(paypoint_id)
            total_sales_amount = Paypoint.get_total_sales_amount(paypoint_id)

            # Log the stats access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='paypoint_stats',
                resource_id=paypoint_id,
                details=f"User accessed Paypoint statistics",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'paypoint_id': paypoint_id,
                'sales_count': sales_count,
                'total_sales_amount': total_sales_amount,
                'status': paypoint.status
            }, 200

        except Exception as e:
            logger.error(f"Error retrieving Paypoint ID {paypoint_id} stats: {str(e)}")
            return {'message': 'Error retrieving Paypoint statistics'}, 500
