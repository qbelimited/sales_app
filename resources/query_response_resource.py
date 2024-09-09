from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.query_model import QueryResponse, Query
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define namespace
query_response_ns = Namespace('query_responses', description='Query responses management')

# Define models for Swagger documentation
query_response_model = query_response_ns.model('QueryResponse', {
    'id': fields.Integer(description='Response ID'),
    'query_id': fields.Integer(description='Query ID'),
    'user_id': fields.Integer(description='User ID'),
    'response': fields.String(required=True, description='Response content'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at'),
})

@query_response_ns.route('/<int:query_id>')
class QueryResponseResource(Resource):
    @query_response_ns.doc(security='Bearer Auth')
    @query_response_ns.marshal_list_with(query_response_model)
    @jwt_required()
    def get(self, query_id):
        """Retrieve all responses to a specific query/feedback."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            return {'message': 'Query/Feedback not found'}, 404

        responses = QueryResponse.query.filter_by(query_id=query_id, is_deleted=False).all()

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='query_response_list',
            resource_id=query_id,
            details=f"User accessed responses to query/feedback with ID {query_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return responses, 200

    @query_response_ns.expect(query_response_model)
    @query_response_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Bad Request'})
    @jwt_required()
    def post(self, query_id):
        """Submit a response to a specific query/feedback."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            return {'message': 'Query/Feedback not found'}, 404

        data = request.json
        if not data.get('response'):
            return {'message': 'Response content is required'}, 400

        try:
            new_response = QueryResponse(
                query_id=query_id,
                user_id=current_user['id'],
                response=data['response'],
                created_at=datetime.utcnow()
            )
            db.session.add(new_response)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error creating response for query ID {query_id}: {str(e)}")
            return {'message': 'Error creating response'}, 500

        # Log the response creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='query_response',
            resource_id=new_response.id,
            details=f"User submitted a response to query/feedback with ID {query_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_response.serialize(), 201

@query_response_ns.route('/<int:query_id>/<int:response_id>')
class QueryResponseByIdResource(Resource):
    @query_response_ns.doc(security='Bearer Auth')
    @query_response_ns.marshal_with(query_response_model)
    @jwt_required()
    def put(self, query_id, response_id):
        """Update a specific response to a query/feedback."""
        current_user = get_jwt_identity()

        response = QueryResponse.query.filter_by(id=response_id, query_id=query_id, is_deleted=False).first()
        if not response:
            return {'message': 'Response not found'}, 404

        if response.user_id != current_user['id'] and current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        try:
            response.response = data.get('response', response.response)
            response.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating response ID {response_id} for query ID {query_id}: {str(e)}")
            return {'message': 'Error updating response'}, 500

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='query_response',
            resource_id=response.id,
            details=f"User updated response to query/feedback with ID {query_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return response.serialize(), 200

    @query_response_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Response not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, query_id, response_id):
        """Soft delete a response to a query/feedback."""
        current_user = get_jwt_identity()

        response = QueryResponse.query.filter_by(id=response_id, query_id=query_id, is_deleted=False).first()
        if not response:
            return {'message': 'Response not found'}, 404

        if response.user_id != current_user['id'] and current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        try:
            response.is_deleted = True
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting response ID {response_id} for query ID {query_id}: {str(e)}")
            return {'message': 'Error deleting response'}, 500

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='query_response',
            resource_id=response.id,
            details=f"User soft-deleted response with ID {response.id} for query/feedback ID {query_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Response deleted successfully'}, 200
