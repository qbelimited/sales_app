from app import db
from datetime import datetime


class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    resolved = db.Column(db.Boolean, default=False, index=True)

    # Relationships
    user = db.relationship('User', backref='queries')
    responses = db.relationship('QueryResponse', backref='query', lazy=True, cascade="all, delete-orphan")

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
    def get_active_queries():
        """Static method to get non-deleted queries."""
        return Query.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_resolved_queries():
        """Static method to get resolved queries."""
        return Query.query.filter_by(resolved=True, is_deleted=False).all()

    @staticmethod
    def get_unresolved_queries():
        """Static method to get unresolved queries."""
        return Query.query.filter_by(resolved=False, is_deleted=False).all()


class QueryResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='responses')

    def serialize(self):
        return {
            'id': self.id,
            'query_id': self.query_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
