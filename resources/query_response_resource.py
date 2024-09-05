from flask_restful import Resource
from flask import request, jsonify
from models.query_model import QueryResponse, Query
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class QueryResponseResource(Resource):
    @jwt_required()
    def get(self, query_id):
        """Retrieve all responses to a specific query/feedback."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            return {'message': 'Query/Feedback not found'}, 404

        responses = QueryResponse.query.filter_by(query_id=query_id).all()

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

        return {
            'query_id': query_id,
            'responses': [response.serialize() for response in responses]
        }, 200

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

        new_response = QueryResponse(
            query_id=query_id,
            user_id=current_user['id'],
            response=data['response'],
            created_at=datetime.utcnow()
        )
        db.session.add(new_response)
        db.session.commit()

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

    @jwt_required()
    def put(self, query_id, response_id):
        """Update a specific response to a query/feedback."""
        current_user = get_jwt_identity()

        response = QueryResponse.query.filter_by(id=response_id, query_id=query_id).first()
        if not response:
            return {'message': 'Response not found'}, 404

        if response.user_id != current_user['id'] and current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        response.response = data.get('response', response.response)
        response.updated_at = datetime.utcnow()

        db.session.commit()

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

    @jwt_required()
    def delete(self, query_id, response_id):
        """Soft delete a response to a query/feedback."""
        current_user = get_jwt_identity()

        response = QueryResponse.query.filter_by(id=response_id, query_id=query_id).first()
        if not response:
            return {'message': 'Response not found'}, 404

        if response.user_id != current_user['id'] and current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        response.is_deleted = True
        db.session.commit()

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
