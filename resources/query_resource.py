from flask_restx import Namespace, Resource, fields
from flask import request
from models.query_model import Query
from models.audit_model import AuditTrail
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip
from sqlalchemy import and_, or_

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
    'resolved': fields.Boolean(description='Whether the query is resolved'),
    'category': fields.String(description='Query category'),
    'priority': fields.Integer(description='Query priority (1-5)')
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role='user'):
    return current_user['role'].lower() in ['admin', required_role]

@query_ns.route('/')
class QueryListResource(Resource):
    @query_ns.doc(security='Bearer Auth')
    @jwt_required()
    @query_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @query_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @query_ns.param('filter_by', 'Filter by content or subject', type='string')
    @query_ns.param('sort_by', 'Sort field', type='string', default='created_at')
    @query_ns.param('category', 'Filter by category', type='string')
    @query_ns.param('resolved', 'Filter by resolved status', type='boolean')
    @query_ns.param('priority', 'Filter by priority', type='integer')
    def get(self):
        """Retrieve a list of all queries/feedback with enhanced filtering."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')
        category = request.args.get('category', None)
        resolved = request.args.get('resolved', None)
        priority = request.args.get('priority', None)

        # Validate sort field
        valid_sort_fields = ['created_at', 'updated_at', 'subject', 'priority', 'resolved']
        if sort_by not in valid_sort_fields:
            logger.error(f"Invalid sorting field: {sort_by}")
            return {'message': f'Invalid sorting field: {sort_by}'}, 400

        # Build query with filters
        query_query = Query.query.filter_by(is_deleted=False)

        # Apply content/subject filter
        if filter_by:
            query_query = query_query.filter(
                or_(
                    Query.content.ilike(f'%{filter_by}%'),
                    Query.subject.ilike(f'%{filter_by}%')
                )
            )

        # Apply category filter
        if category:
            query_query = query_query.filter_by(category=category)

        # Apply resolved filter
        if resolved is not None:
            query_query = query_query.filter_by(resolved=resolved.lower() == 'true')

        # Apply priority filter
        if priority:
            try:
                priority = int(priority)
                if 1 <= priority <= 5:
                    query_query = query_query.filter_by(priority=priority)
                else:
                    return {'message': 'Priority must be between 1 and 5'}, 400
            except ValueError:
                return {'message': 'Invalid priority value'}, 400

        try:
            queries = query_query.order_by(getattr(Query, sort_by).desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
        except Exception as e:
            logger.error(f"Error fetching query list: {str(e)}")
            return {'message': 'Error fetching query list'}, 500

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='query_list',
            details="User accessed list of queries/feedback",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
        """Submit a new query/feedback with enhanced validation."""
        current_user = get_jwt_identity()
        data = request.json

        # Validate required fields
        if not data.get('content'):
            logger.error(f"Query content missing for User ID {current_user['id']}")
            return {'message': 'Query/Feedback content is required'}, 400

        # Validate priority if provided
        if 'priority' in data:
            try:
                priority = int(data['priority'])
                if not 1 <= priority <= 5:
                    return {'message': 'Priority must be between 1 and 5'}, 400
            except ValueError:
                return {'message': 'Invalid priority value'}, 400

        try:
            new_query = Query(
                user_id=current_user['id'],
                content=data['content'],
                subject=data.get('subject', ''),
                category=data.get('category'),
                priority=data.get('priority', 1),
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
            details=f"User submitted a new query/feedback with ID {new_query.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
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
        """Retrieve a single query/feedback by ID with responses."""
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
            details=f"User accessed query/feedback with ID {query_id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return query.serialize(), 200

    @query_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Query Not Found', 403: 'Unauthorized'})
    @jwt_required()
    @query_ns.expect(query_model, validate=True)
    def put(self, query_id):
        """Update an existing query/feedback with enhanced validation."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            logger.warning(f"Query ID {query_id} not found for update by User ID {current_user['id']}")
            return {'message': 'Query/Feedback not found'}, 404

        # Check authorization
        if not check_role_permission(current_user) and query.user_id != current_user['id']:
            logger.warning(f"Unauthorized update attempt on Query ID {query_id} by User ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate priority if provided
        if 'priority' in data:
            try:
                priority = int(data['priority'])
                if not 1 <= priority <= 5:
                    return {'message': 'Priority must be between 1 and 5'}, 400
            except ValueError:
                return {'message': 'Invalid priority value'}, 400

        try:
            query.content = data.get('content', query.content)
            query.subject = data.get('subject', query.subject)
            query.category = data.get('category', query.category)
            query.priority = data.get('priority', query.priority)
            query.resolved = data.get('resolved', query.resolved)
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
            details=f"User updated query/feedback with ID {query.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Query/feedback ID {query.id} updated by User ID {current_user['id']}")
        return query.serialize(), 200

    @query_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Query Not Found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, query_id):
        """Soft delete a query/feedback with authorization check."""
        current_user = get_jwt_identity()

        query = Query.query.filter_by(id=query_id, is_deleted=False).first()
        if not query:
            logger.warning(f"Query ID {query_id} not found for delete by User ID {current_user['id']}")
            return {'message': 'Query/Feedback not found'}, 404

        # Check authorization
        if not check_role_permission(current_user) and query.user_id != current_user['id']:
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
            details=f"User soft-deleted query/feedback with ID {query.id}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Query/feedback ID {query.id} soft-deleted by User ID {current_user['id']}")
        return {'message': 'Query/Feedback deleted successfully'}, 200
