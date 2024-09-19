from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Query(db.Model):
    __tablename__ = 'query'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    resolved = db.Column(db.Boolean, default=False, index=True)

    # Relationships
    user = db.relationship('User', backref='queries')
    responses = db.relationship('QueryResponse', backref='query', lazy=True, cascade="all, delete-orphan")

    @validates('content')
    def validate_content(self, key, content):
        if not content or content.strip() == "":
            raise ValueError("Query content cannot be empty")
        return content

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
            'resolved': self.resolved,
            'responses': [response.serialize() for response in self.responses]
        }

    @staticmethod
    def get_active_queries(page=1, per_page=10, sort_by='created_at', ascending=True):
        """Retrieve paginated list of active queries with sorting."""
        query = Query.query.filter_by(is_deleted=False)
        if sort_by not in ['created_at', 'subject', 'resolved']:
            raise ValueError(f"Invalid sort_by field: {sort_by}")
        order_by = getattr(Query, sort_by)
        if not ascending:
            order_by = order_by.desc()
        return query.order_by(order_by).paginate(page=page, per_page=per_page, error_out=False).items

    @staticmethod
    def get_resolved_queries(page=1, per_page=10, sort_by='created_at', ascending=True):
        """Retrieve paginated list of resolved queries with sorting."""
        query = Query.query.filter_by(resolved=True, is_deleted=False)
        order_by = getattr(Query, sort_by)
        if not ascending:
            order_by = order_by.desc()
        return query.order_by(order_by).paginate(page=page, per_page=per_page, error_out=False).items

    @staticmethod
    def get_unresolved_queries(page=1, per_page=10, sort_by='created_at', ascending=True):
        """Retrieve paginated list of unresolved queries with sorting."""
        query = Query.query.filter_by(resolved=False, is_deleted=False)
        order_by = getattr(Query, sort_by)
        if not ascending:
            order_by = order_by.desc()
        return query.order_by(order_by).paginate(page=page, per_page=per_page, error_out=False).items

class QueryResponse(db.Model):
    __tablename__ = 'query_response'

    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='responses')

    @validates('content')
    def validate_content(self, key, content):
        if not content or content.strip() == "":
            raise ValueError("Response content cannot be empty")
        return content

    def serialize(self):
        return {
            'id': self.id,
            'query_id': self.query_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }

    @staticmethod
    def get_responses_by_query(query_id):
        """Retrieve all responses associated with a specific query."""
        return QueryResponse.query.filter_by(query_id=query_id).all()
