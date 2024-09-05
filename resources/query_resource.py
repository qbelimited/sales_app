from flask_restful import Resource
from flask import request, jsonify
from models.query_model import Query
from models.audit_model import AuditTrail
from models.user_model import User
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class QueryResource(Resource):
    @jwt_required()
    def get(self, query_id=None):
        """Retrieve a query/feedback or list of all queries/feedback."""
        current_user = get_jwt_identity()

        if query_id:
            query = Query.query.filter_by(id=query_id).first()
            if not query:
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
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            query_query = Query.query

            if filter_by:
                query_query = query_query.filter(Query.content.ilike(f'%{filter_by}%'))

            queries = query_query.order_by(sort_by).paginate(page, per_page, error_out=False)

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

    @jwt_required()
    def post(self):
        """Submit a new query/feedback."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate required fields
        if not data.get('content'):
            return {'message': 'Query/Feedback content is required'}, 400

        new_query = Query(
            user_id=current_user['id'],
            content=data['content'],
            subject=data.get('subject', ''),
            created_at=datetime.utcnow()
        )
        db.session.add(new_query)
        db.session.commit()

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

        return new_query.serialize(), 201

    @jwt_required()
    def put(self, query_id):
        """Update an existing query/feedback."""
        current_user = get_jwt_identity()
        query = Query.query.filter_by(id=query_id).first()
        if not query:
            return {'message': 'Query/Feedback not found'}, 404

        if query.user_id != current_user['id'] and current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        data = request.json
        query.content = data.get('content', query.content)
        query.subject = data.get('subject', query.subject)
        query.updated_at = datetime.utcnow()

        db.session.commit()

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

        return query.serialize(), 200

    @jwt_required()
    def delete(self, query_id):
        """Soft delete a query/feedback."""
        current_user = get_jwt_identity()
        query = Query.query.filter_by(id=query_id).first()
        if not query:
            return {'message': 'Query/Feedback not found'}, 404

        if query.user_id != current_user['id'] and current_user['role'] != 'admin':
            return {'message': 'Unauthorized'}, 403

        query.is_deleted = True
        db.session.commit()

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

        return {'message': 'Query/Feedback deleted successfully'}, 200
