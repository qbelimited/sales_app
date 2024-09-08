from app import db
from datetime import datetime


# RetentionPolicy model to manage the retention period of audit logs
class RetentionPolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    retention_days = db.Column(db.Integer, nullable=False, default=365)  # Default retention period of 1 year
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'retention_days': self.retention_days,
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def get_current_policy():
        """Fetches the current retention policy or sets a default if none exists."""
        policy = RetentionPolicy.query.first()
        if not policy:
            # If no retention policy exists, create one with default values
            policy = RetentionPolicy(retention_days=365)
            db.session.add(policy)
            db.session.commit()
        return policy

