from app import db
from datetime import datetime
from sqlalchemy.orm import validates


class RetentionPolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    retention_days = db.Column(db.Integer, nullable=False, default=365)  # Default retention period of 1 year
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Timestamp when the policy is created
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('id', name='_single_retention_policy_uc'),)  # Ensure only one policy exists

    @validates('retention_days')
    def validate_retention_days(self, _, retention_days):
        if retention_days <= 0:
            raise ValueError("Retention days must be a positive integer")
        return retention_days

    def serialize(self):
        """Serialize the RetentionPolicy object for easy representation."""
        return {
            'id': self.id,
            'retention_days': self.retention_days,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @staticmethod
    def get_current_policy():
        """Fetches the current retention policy or creates one with default values if none exists."""
        try:
            policy = RetentionPolicy.query.first()

            # If no policy exists, create a default one with 365 days retention period
            if not policy:
                policy = RetentionPolicy(retention_days=365)
                db.session.add(policy)
                db.session.commit()
                db.session.refresh(policy)  # Ensure the new policy is reflected in the current session

            return policy

        except Exception as e:
            db.session.rollback()  # Roll back any uncommitted transactions in case of error
            raise ValueError(f"Error fetching or creating retention policy: {e}")

    @staticmethod
    def update_retention_days(new_retention_days):
        """Updates the retention days for the current policy."""
        try:
            policy = RetentionPolicy.get_current_policy()
            policy.retention_days = new_retention_days
            db.session.commit()
            return policy

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error updating retention policy: {e}")
