from extensions import db
from datetime import datetime
from sqlalchemy.orm import validates
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import and_, or_

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
    category = db.Column(db.String(50), nullable=True, index=True)
    priority = db.Column(db.Integer, default=1)

    # Relationships
    user = db.relationship('User', backref='queries')
    responses = db.relationship('QueryResponse', backref='query', lazy=True, cascade="all, delete-orphan")

    @validates('content')
    def validate_content(self, key: str, content: str) -> str:
        if not content or content.strip() == "":
            raise ValueError("Query content cannot be empty")
        return content

    def serialize(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
            'resolved': self.resolved,
            'category': self.category,
            'priority': self.priority,
            'responses': [response.serialize() for response in self.responses]
        }

    @staticmethod
    def get_active_queries(
        page: int = 1,
        per_page: int = 10,
        sort_by: str = 'created_at',
        ascending: bool = True
    ) -> List['Query']:
        """Retrieve paginated list of active queries with sorting."""
        query = Query.query.filter_by(is_deleted=False)
        if sort_by not in ['created_at', 'subject', 'resolved', 'priority']:
            raise ValueError(f"Invalid sort_by field: {sort_by}")
        order_by = getattr(Query, sort_by)
        if not ascending:
            order_by = order_by.desc()
        return query.order_by(order_by).paginate(page=page, per_page=per_page, error_out=False).items

    @staticmethod
    def search_queries(
        search_term: str,
        category: Optional[str] = None,
        resolved: Optional[bool] = None
    ) -> List['Query']:
        """Search queries by content, subject, and optional filters."""
        query = Query.query.filter(
            and_(
                Query.is_deleted == False,
                or_(
                    Query.content.ilike(f'%{search_term}%'),
                    Query.subject.ilike(f'%{search_term}%')
                )
            )
        )
        if category:
            query = query.filter(Query.category == category)
        if resolved is not None:
            query = query.filter(Query.resolved == resolved)
        return query.all()

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
    is_helpful = db.Column(db.Boolean, default=None)
    rating = db.Column(db.Integer, nullable=True)

    # Relationships
    user = db.relationship('User', backref='responses')

    @validates('content')
    def validate_content(self, key: str, content: str) -> str:
        if not content or content.strip() == "":
            raise ValueError("Response content cannot be empty")
        return content

    @validates('rating')
    def validate_rating(self, key: str, rating: Optional[int]) -> Optional[int]:
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")
        return rating

    def serialize(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'query_id': self.query_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'is_helpful': self.is_helpful,
            'rating': self.rating
        }

    @staticmethod
    def get_responses_by_query(query_id: int) -> List['QueryResponse']:
        """Retrieve all responses associated with a specific query."""
        return QueryResponse.query.filter_by(query_id=query_id).all()

    @staticmethod
    def get_helpful_responses(query_id: int) -> List['QueryResponse']:
        """Retrieve all helpful responses for a specific query."""
        return QueryResponse.query.filter_by(
            query_id=query_id,
            is_helpful=True
        ).all()

    @staticmethod
    def get_average_rating(query_id: int) -> float:
        """Calculate the average rating for responses to a query."""
        result = db.session.query(
            db.func.avg(QueryResponse.rating)
        ).filter_by(
            query_id=query_id
        ).scalar()
        return float(result) if result else 0.0
