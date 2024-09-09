from app import db
from datetime import datetime
from sqlalchemy.orm import validates


class RetentionPolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    retention_days = db.Column(db.Integer, nullable=False, default=365)  # Default retention period of 1 year
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @validates('retention_days')
    def validate_retention_days(self, _, retention_days):
        if retention_days <= 0:
            raise ValueError("Retention days must be a positive integer")
        return retention_days

    def serialize(self):
        return {
            'id': self.id,
            'retention_days': self.retention_days,
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def get_current_policy():
        """Fetches the current retention policy or sets a default if none exists."""
        try:
            policy = RetentionPolicy.query.first()
            if not policy:
                # If no retention policy exists, create one with default values
                policy = RetentionPolicy(retention_days=365)
                db.session.add(policy)
                db.session.commit()
            return policy
        except Exception as e:
            raise ValueError(f"Error fetching or creating retention policy: {e}")
