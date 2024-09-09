from flask_restx import Namespace, Resource, fields
from flask import request, jsonify
from models.query_model import Query
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for the queries
query_ns = Namespace('queries', description='Operations related to queries and feedback')

# Define models for Swagger documentation
query_model = query_ns.model('Query', {
    'id': fields.Integer(description='Query ID'),
    'content': fields.String(required=True, description='Query/Feedback content'),
    'subject': fields.String(description='Query/Feedback subject'),
    'user_id': fields.Integer(description='User ID'),
    'created_at': fields.String(description='Created At'),
    'updated_at': fields.String(description='Updated At'),
})

@query_ns.route('/')
class QueryListResource(Resource):
    @query_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Retrieve a list of all queries/feedback."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        valid_sort_fields = ['created_at', 'updated_at', 'subject']
        if sort_by not in valid_sort_fields:
            logger.error(f"Invalid sorting field: {sort_by}")
            return {'message': f'Invalid sorting field: {sort_by}'}, 400

        query_query = Query.query.filter_by(is_deleted=False)

        if filter_by:
            query_query = query_query.filter(Query.content.ilike(f'%{filter_by}%'))

        try:
            queries = query_query.order_by(getattr(Query, sort_by).desc()).paginate(page, per_page, error_out=False)
        except Exception as e:
            logger.error(f"Error fetching query list: {str(e)}")
            return {'message': 'Error fetching query list'}, 500

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='query_list',
            resource_id=None,
            details=f"User accessed list of queries/feedback"
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'queries': [query.serialize() for query in queries.items],
            'total': queries.total,
            'pages': queries.pages,
            'current_page': queries.page
        }, 200

    @query_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Invalid Input'})
    @jwt_required()
    @query_ns.expect(query_model, validate=True)
    def post(self):
        """Submit a new query/feedback."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate required fields
        if not data.get('content'):
            logger.error(f"Query content missing for User ID {current_user['id']}")
            return {'message': 'Query/Feedback content is required'}, 400

        try:
            new_query = Query(
                user_id=current_user['id'],
                content=data['content'],
                subject=data.get('subject', ''),
                created_at=datetime.utcnow()
            )
            db.session.add(new_query)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error creating query for User ID {current_user['id']}: {str(e)}")
            return {'message': 'Error creating query'}, 500

        # Log the query creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='query',
            resource_id=new_query.id,
            details=f"User submitted a new query/feedback with ID {new_query.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"New query/feedback created with ID {new_query.id} by User ID {current_user['id']}")
        return new_query.serialize(), 201

@query_ns.route('/<int:query_id>')
class QueryResource(Resource):
    @query_ns.doc(security='Bearer Auth', responses={200: 'OK', 404: 'Query Not Found'})
    @jwt_required()
    def get(self, query_id):
        """Retrieve a single query/feedback by ID."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            logger.warning(f"Query ID {query_id} not found for User ID {current_user['id']}")
            return {'message': 'Query/Feedback not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='query',
            resource_id=query_id,
            details=f"User accessed query/feedback with ID {query_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return query.serialize(), 200

    @query_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Query Not Found', 403: 'Unauthorized'})
    @jwt_required()
    @query_ns.expect(query_model, validate=True)
    def put(self, query_id):
        """Update an existing query/feedback."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            logger.warning(f"Query ID {query_id} not found for update by User ID {current_user['id']}")
            return {'message': 'Query/Feedback not found'}, 404

        if query.user_id != current_user['id'] and current_user['role'] != 'admin':
            logger.warning(f"Unauthorized update attempt on Query ID {query_id} by User ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        try:
            query.content = data.get('content', query.content)
            query.subject = data.get('subject', query.subject)
            query.updated_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating query ID {query_id}: {str(e)}")
            return {'message': 'Error updating query'}, 500

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='query',
            resource_id=query.id,
            details=f"User updated query/feedback with ID {query.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Query/feedback ID {query.id} updated by User ID {current_user['id']}")
        return query.serialize(), 200

    @query_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Query Not Found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, query_id):
        """Soft delete a query/feedback."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            logger.warning(f"Query ID {query_id} not found for delete by User ID {current_user['id']}")
            return {'message': 'Query/Feedback not found'}, 404

        if query.user_id != current_user['id'] and current_user['role'] != 'admin':
            logger.warning(f"Unauthorized delete attempt on Query ID {query_id} by User ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        try:
            query.is_deleted = True
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting query ID {query_id}: {str(e)}")
            return {'message': 'Error deleting query'}, 500

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='query',
            resource_id=query.id,
            details=f"User soft-deleted query/feedback with ID {query.id}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Query/feedback ID {query.id} soft-deleted by User ID {current_user['id']}")
        return {'message': 'Query/Feedback deleted successfully'}, 200
