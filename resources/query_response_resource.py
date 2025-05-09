from flask_restx import Namespace, Resource, fields
from flask import request
from models.query_model import QueryResponse, Query
from models.audit_model import AuditTrail
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip
from sqlalchemy import and_, or_

# Define namespace
query_response_ns = Namespace('query_responses', description='Query responses management')

# Define models for Swagger documentation
query_response_model = query_response_ns.model('QueryResponse', {
    'id': fields.Integer(description='Response ID'),
    'query_id': fields.Integer(description='Query ID'),
    'user_id': fields.Integer(description='User ID'),
    'content': fields.String(required=True, description='Response content'),
    'created_at': fields.DateTime(description='Created at'),
    'updated_at': fields.DateTime(description='Updated at'),
    'status': fields.String(description='Response status', enum=['draft', 'published', 'archived']),
    'is_solution': fields.Boolean(description='Whether this response solves the query'),
    'attachments': fields.List(fields.String, description='List of attachment URLs')
})

# Helper function to check if the user is an admin or the owner of the resource
def check_user_authorization(current_user, resource_user_id):
    return current_user['role'].lower() == 'admin' or current_user['id'] == resource_user_id

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
            logger.warning(f"Query ID {query_id} not found for User ID {current_user['id']}.")
            return {'message': 'Query/Feedback not found'}, 404

        # Get responses with optional filtering
        status = request.args.get('status')
        is_solution = request.args.get('is_solution')

        query_responses = QueryResponse.query.filter_by(query_id=query_id)

        if status:
            query_responses = query_responses.filter_by(status=status)
        if is_solution is not None:
            query_responses = query_responses.filter_by(is_solution=is_solution.lower() == 'true')

        responses = query_responses.order_by(QueryResponse.created_at.desc()).all()

        # Log the access to the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='query_response_list',
            resource_id=query_id,
            details=f"User accessed responses to query/feedback with ID {query_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
            logger.warning(f"Query ID {query_id} not found for User ID {current_user['id']}.")
            return {'message': 'Query/Feedback not found'}, 404

        data = request.json
        if not data.get('content'):
            logger.error(f"Missing response content for User ID {current_user['id']} in Query ID {query_id}.")
            return {'message': 'Response content is required'}, 400

        # Validate status if provided
        if 'status' in data and data['status'] not in ['draft', 'published', 'archived']:
            return {'message': 'Invalid status value'}, 400

        try:
            new_response = QueryResponse(
                query_id=query_id,
                user_id=current_user['id'],
                content=data['content'],
                status=data.get('status', 'published'),
                is_solution=data.get('is_solution', False),
                attachments=data.get('attachments', []),
                created_at=datetime.utcnow()
            )
            db.session.add(new_response)

            # If this is marked as a solution, update the query status
            if new_response.is_solution:
                query.resolved = True
                query.updated_at = datetime.utcnow()

            db.session.commit()
        except Exception as e:
            logger.error(f"Error creating response for query ID {query_id} by User ID {current_user['id']}: {str(e)}")
            return {'message': 'Error creating response'}, 500

        # Log the response creation to the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='query_response',
            resource_id=new_response.id,
            details=f"User submitted a response to query/feedback with ID {query_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Response created for Query ID {query_id} by User ID {current_user['id']}.")
        return new_response.serialize(), 201

@query_response_ns.route('/<int:query_id>/<int:response_id>')
class QueryResponseByIdResource(Resource):
    @query_response_ns.doc(security='Bearer Auth')
    @query_response_ns.marshal_with(query_response_model)
    @jwt_required()
    def put(self, query_id, response_id):
        """Update a specific response to a query/feedback."""
        current_user = get_jwt_identity()

        response = QueryResponse.query.filter_by(id=response_id, query_id=query_id).first()
        if not response:
            logger.warning(f"Response ID {response_id} not found for Query ID {query_id} by User ID {current_user['id']}.")
            return {'message': 'Response not found'}, 404

        if not check_user_authorization(current_user, response.user_id):
            logger.warning(f"Unauthorized update attempt on Response ID {response_id} for Query ID {query_id} by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate status if provided
        if 'status' in data and data['status'] not in ['draft', 'published', 'archived']:
            return {'message': 'Invalid status value'}, 400

        try:
            response.content = data.get('content', response.content)
            response.status = data.get('status', response.status)
            response.is_solution = data.get('is_solution', response.is_solution)
            response.attachments = data.get('attachments', response.attachments)
            response.updated_at = datetime.utcnow()

            # If this is marked as a solution, update the query status
            if response.is_solution:
                query = Query.query.get(query_id)
                if query:
                    query.resolved = True
                    query.updated_at = datetime.utcnow()

            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating response ID {response_id} for query ID {query_id} by User ID {current_user['id']}: {str(e)}")
            return {'message': 'Error updating response'}, 500

        # Log the update to the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='query_response',
            resource_id=response.id,
            details=f"User updated response to query/feedback with ID {query_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Response ID {response_id} for Query ID {query_id} updated by User ID {current_user['id']}.")
        return response.serialize(), 200

    @query_response_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Response not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, query_id, response_id):
        """Soft delete a response to a query/feedback."""
        current_user = get_jwt_identity()

        response = QueryResponse.query.filter_by(id=response_id, query_id=query_id).first()
        if not response:
            logger.warning(f"Response ID {response_id} not found for Query ID {query_id} by User ID {current_user['id']}.")
            return {'message': 'Response not found'}, 404

        if not check_user_authorization(current_user, response.user_id):
            logger.warning(f"Unauthorized delete attempt on Response ID {response_id} for Query ID {query_id} by User ID {current_user['id']}.")
            return {'message': 'Unauthorized'}, 403

        try:
            response.is_deleted = True
            response.updated_at = datetime.utcnow()

            # If this was a solution, check if there are other solutions
            if response.is_solution:
                query = Query.query.get(query_id)
                if query:
                    other_solutions = QueryResponse.query.filter_by(
                        query_id=query_id,
                        is_solution=True,
                        is_deleted=False
                    ).count()
                    if other_solutions == 0:
                        query.resolved = False
                        query.updated_at = datetime.utcnow()

            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting response ID {response_id} for query ID {query_id} by User ID {current_user['id']}: {str(e)}")
            return {'message': 'Error deleting response'}, 500

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='query_response',
            resource_id=response.id,
            details=f"User soft-deleted response with ID {response.id} for query/feedback ID {query_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Response ID {response_id} for Query ID {query_id} soft-deleted by User ID {current_user['id']}.")
        return {'message': 'Response deleted successfully'}, 200
