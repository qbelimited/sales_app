from extensions import db
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
from typing import Optional, Dict, List, Any
from enum import Enum
import json
import gzip
from sqlalchemy import event


class DataType(Enum):
    """Types of data that can have retention policies."""
    SALES = 'sales'
    AUDIT = 'audit'
    REPORTS = 'reports'
    PERFORMANCE = 'performance'
    USER_SESSIONS = 'user_sessions'
    CUSTOM = 'custom'


class DataImportance(Enum):
    """Importance levels for data retention."""
    CRITICAL = 'critical'  # Must be retained longer
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'  # Can be deleted sooner


class ArchivedData(db.Model):
    """Model for storing archived data before deletion."""
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50), nullable=False, index=True)
    original_id = db.Column(db.Integer, nullable=False)
    original_data = db.Column(db.LargeBinary, nullable=False)  # Compressed JSON
    archived_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    retention_policy_id = db.Column(
        db.Integer,
        db.ForeignKey('retention_policy.id'),
        nullable=False
    )
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    retention_policy = db.relationship('RetentionPolicy', backref='archived_data')

    def compress_data(self, data: Dict) -> None:
        """Compress and store the data."""
        json_data = json.dumps(data)
        self.original_data = gzip.compress(json_data.encode())

    def decompress_data(self) -> Dict:
        """Decompress and return the original data."""
        return json.loads(gzip.decompress(self.original_data).decode())


class RetentionPolicy(db.Model):
    """Model for managing data retention policies."""
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(
        db.String(50),
        nullable=False,
        default=DataType.SALES.value,
        index=True
    )
    importance = db.Column(
        db.String(20),
        nullable=False,
        default=DataImportance.MEDIUM.value,
        index=True
    )
    retention_days = db.Column(db.Integer, nullable=False, default=365)
    archive_before_delete = db.Column(db.Boolean, default=True)
    max_retention_days = db.Column(db.Integer, nullable=True)
    notification_days = db.Column(db.Integer, nullable=True)  # Days before expiration to notify
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            'data_type',
            name='_single_retention_policy_per_type_uc'
        ),
    )

    @validates('retention_days')
    def validate_retention_days(self, _, retention_days):
        """Validate retention days."""
        if retention_days <= 0:
            raise ValueError("Retention days must be positive")
        if self.max_retention_days and retention_days > self.max_retention_days:
            raise ValueError(
                f"Retention days cannot exceed {self.max_retention_days}"
            )
        return retention_days

    @validates('data_type', 'importance')
    def validate_enums(self, key, value):
        """Validate enum values."""
        try:
            if key == 'data_type':
                DataType(value)
            else:
                DataImportance(value)
        except ValueError:
            raise ValueError(f"Invalid {key}: {value}")
        return value

    def serialize(self) -> Dict:
        """Serialize the RetentionPolicy object."""
        return {
            'id': self.id,
            'data_type': self.data_type,
            'importance': self.importance,
            'retention_days': self.retention_days,
            'archive_before_delete': self.archive_before_delete,
            'max_retention_days': self.max_retention_days,
            'notification_days': self.notification_days,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def is_data_expired(self, data_date: datetime) -> bool:
        """Check if data is expired."""
        if not data_date:
            return False
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        return data_date < cutoff_date

    def should_notify(self, data_date: datetime) -> bool:
        """Check if notification should be sent."""
        if not self.notification_days or not data_date:
            return False
        notification_date = datetime.utcnow() + timedelta(days=self.notification_days)
        return data_date < notification_date

    @staticmethod
    def get_policy(data_type: str) -> 'RetentionPolicy':
        """Get retention policy for a data type."""
        try:
            policy = RetentionPolicy.query.filter_by(
                data_type=data_type
            ).first()

            if not policy:
                policy = RetentionPolicy(
                    data_type=data_type,
                    retention_days=365
                )
                db.session.add(policy)
                db.session.commit()
                db.session.refresh(policy)

            return policy

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error fetching retention policy: {e}")

    @staticmethod
    def update_policy(
        data_type: str,
        retention_days: int,
        importance: Optional[str] = None,
        archive_before_delete: Optional[bool] = None,
        max_retention_days: Optional[int] = None,
        notification_days: Optional[int] = None
    ) -> 'RetentionPolicy':
        """Update retention policy."""
        try:
            policy = RetentionPolicy.get_policy(data_type)
            policy.retention_days = retention_days
            if importance is not None:
                policy.importance = importance
            if archive_before_delete is not None:
                policy.archive_before_delete = archive_before_delete
            if max_retention_days is not None:
                policy.max_retention_days = max_retention_days
            if notification_days is not None:
                policy.notification_days = notification_days
            db.session.commit()
            return policy

        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error updating retention policy: {e}")

    @staticmethod
    def get_all_policies() -> List['RetentionPolicy']:
        """Get all retention policies."""
        return RetentionPolicy.query.all()

    @staticmethod
    def get_expired_data_cutoff(data_type: str) -> Optional[datetime]:
        """Get cutoff date for expired data."""
        try:
            policy = RetentionPolicy.get_policy(data_type)
            return datetime.utcnow() - timedelta(days=policy.retention_days)
        except Exception:
            return None

    @staticmethod
    def get_data_volume(data_type: str) -> Dict[str, Any]:
        """Get data volume statistics."""
        try:
            policy = RetentionPolicy.get_policy(data_type)
            cutoff_date = policy.get_expired_data_cutoff(data_type)

            # Get total records
            total_count = ArchivedData.query.filter_by(
                data_type=data_type,
                is_deleted=False
            ).count()

            # Get records approaching expiration
            expiring_count = ArchivedData.query.filter(
                ArchivedData.data_type == data_type,
                ArchivedData.archived_at < cutoff_date,
                ArchivedData.is_deleted == False
            ).count()

            return {
                'total_records': total_count,
                'expiring_records': expiring_count,
                'retention_days': policy.retention_days,
                'data_type': data_type
            }
        except Exception as e:
            logger.error(f"Error getting data volume: {e}")
            return {}


# Event listeners for automatic retention policy application
@event.listens_for(RetentionPolicy, 'after_insert')
def apply_retention_policy(mapper, connection, target):
    """Apply retention policy to existing data after policy creation."""
    try:
        # Get the model class for the data type
        model_class = globals().get(target.data_type.capitalize())
        if model_class and hasattr(model_class, 'created_at'):
            # Update existing records
            connection.execute(
                model_class.__table__.update()
                .where(model_class.created_at < datetime.utcnow() - timedelta(days=target.retention_days))
                .values(is_deleted=True)
            )
    except Exception as e:
        logger.error(f"Error applying retention policy: {e}")
