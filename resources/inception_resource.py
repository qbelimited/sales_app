from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.inception_model import Inception
from models.sales_model import Sale
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for Inception operations
inception_ns = Namespace('inceptions', description='Operations related to sales inceptions')

# Define the model for Swagger documentation
inception_model = inception_ns.model('Inception', {
    'id': fields.Integer(description='Inception ID'),
    'sale_id': fields.Integer(required=True, description='Sale ID associated with the inception'),
    'amount_received': fields.Float(required=True, description='Amount received in the inception'),
    'received_at': fields.DateTime(description='Date the amount was received'),
    'description': fields.String(description='Description of the inception'),
})

# Inception List Resource (Create new Inception, Get list of Inceptions)
@inception_ns.route('/')
class InceptionListResource(Resource):
    @inception_ns.doc(security='Bearer Auth')
    @inception_ns.marshal_list_with(inception_model)
    @jwt_required()
    def get(self):
        """Retrieve a list of all inceptions."""
        current_user = get_jwt_identity()

        inceptions = Inception.query.all()

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='inception_list',
            resource_id=None,
            details="User accessed list of inceptions"
        )
        db.session.add(audit)
        db.session.commit()

        return inceptions, 200

    @inception_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Invalid Input'})
    @inception_ns.expect(inception_model, validate=True)
    @jwt_required()
    def post(self):
        """Create a new Inception for a sale."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate the Sale exists
        sale = Sale.query.filter_by(id=data['sale_id'], is_deleted=False).first()
        if not sale:
            logger.error(f"Sale with ID {data['sale_id']} not found for user {current_user['id']}")
            return {'message': 'Sale not found'}, 404

        try:
            new_inception = Inception(
                sale_id=data['sale_id'],
                amount_received=data['amount_received'],
                description=data.get('description', ''),
                received_at=data.get('received_at', datetime.utcnow())
            )
            db.session.add(new_inception)
            db.session.commit()

            # Log the creation to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='inception',
                resource_id=new_inception.id,
                details=f"User created a new inception for Sale ID {data['sale_id']}"
            )
            db.session.add(audit)
            db.session.commit()

            logger.info(f"User {current_user['id']} created a new inception for Sale ID {data['sale_id']}")
            return new_inception.serialize(), 201

        except Exception as e:
            logger.error(f"Error creating inception for Sale ID {data['sale_id']}: {str(e)}")
            return {'message': 'Error creating inception'}, 500


# Inception Detail Resource (Get, Update, Delete Inception by ID)
@inception_ns.route('/<int:inception_id>')
class InceptionResource(Resource):
    @inception_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Inception not found'})
    @inception_ns.marshal_with(inception_model)
    @jwt_required()
    def get(self, inception_id):
        """Retrieve a specific Inception by ID."""
        current_user = get_jwt_identity()

        inception = Inception.query.filter_by(id=inception_id).first()
        if not inception:
            logger.error(f"Inception with ID {inception_id} not found for user {current_user['id']}")
            return {'message': 'Inception not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='inception',
            resource_id=inception.id,
            details=f"User accessed inception with ID {inception_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return inception.serialize(), 200

    @inception_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Inception not found', 400: 'Invalid Input'})
    @inception_ns.expect(inception_model, validate=True)
    @jwt_required()
    def put(self, inception_id):
        """Update an existing Inception by ID."""
        current_user = get_jwt_identity()
        data = request.json

        inception = Inception.query.filter_by(id=inception_id).first()
        if not inception:
            logger.error(f"Inception with ID {inception_id} not found for user {current_user['id']}")
            return {'message': 'Inception not found'}, 404

        # Update fields
        inception.amount_received = data.get('amount_received', inception.amount_received)
        inception.description = data.get('description', inception.description)
        inception.received_at = data.get('received_at', inception.received_at)
        inception.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='inception',
            resource_id=inception.id,
            details=f"User updated inception with ID {inception_id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"User {current_user['id']} updated inception with ID {inception_id}")
        return inception.serialize(), 200

    @inception_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Inception not found'})
    @jwt_required()
    def delete(self, inception_id):
        """Delete an Inception by marking it as deleted."""
        current_user = get_jwt_identity()

        inception = Inception.query.filter_by(id=inception_id).first()
        if not inception:
            logger.error(f"Inception with ID {inception_id} not found for user {current_user['id']}")
            return {'message': 'Inception not found'}, 404

        db.session.delete(inception)
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='inception',
            resource_id=inception.id,
            details=f"User deleted inception with ID {inception_id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"User {current_user['id']} deleted inception with ID {inception_id}")
        return {'message': 'Inception deleted successfully'}, 200