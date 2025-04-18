from extensions import db
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import and_


class AuditAction(Enum):
    """Enumeration of possible audit actions in the system."""
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    FILTER = 'FILTER'
    GENERATE_REPORT = 'GENERATE_REPORT'
    REVOKE_REFRESH_TOKEN = 'REVOKE_REFRESH_TOKEN'
    ACCESS = 'ACCESS'


class AuditTrail(db.Model):
    """
    Model for tracking and storing audit logs of system activities.
    Supports archiving of old logs and provides various query methods.
    """
    __tablename__ = 'audit_trail'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='SET NULL'),
        nullable=False,
        index=True
    )
    action = db.Column(db.Enum(AuditAction), nullable=False)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.Integer, nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='audit_trails')

    __table_args__ = (
        db.Index('idx_audit_resource', 'resource_type', 'resource_id'),
        db.Index('idx_audit_user_action', 'user_id', 'action'),
        db.Index('idx_audit_timestamp_archived', 'timestamp', 'is_archived'),
    )

    def serialize(self) -> Dict[str, Any]:
        """Serialize audit trail entry for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action.value,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_archived': self.is_archived,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None
        }

    @staticmethod
    def log_action(
        user_id: int,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[int] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> 'AuditTrail':
        """
        Log an audit action in the system.

        Args:
            user_id: ID of the user performing the action
            action: Type of action being performed
            resource_type: Type of resource being affected
            resource_id: ID of the resource (if applicable)
            old_value: Previous value before the action
            new_value: New value after the action
            details: Additional details about the action
            ip_address: IP address of the user
            user_agent: User agent string from the request

        Returns:
            The created AuditTrail entry

        Raises:
            ValueError: If logging fails
        """
        if not isinstance(action, AuditAction):
            raise ValueError("Action must be an AuditAction enum value")

        audit_entry = AuditTrail(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(audit_entry)
        try:
            db.session.commit()
            return audit_entry
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error logging audit action: {e}")

    @staticmethod
    def archive_old_logs(days: int = 90) -> int:
        """
        Archive audit logs older than specified number of days.

        Args:
            days: Number of days after which logs should be archived

        Returns:
            Number of logs archived
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logs_to_archive = AuditTrail.query.filter(
            and_(
                AuditTrail.timestamp < cutoff_date,
                AuditTrail.is_archived.is_(False)
            )
        ).all()

        for log in logs_to_archive:
            log.is_archived = True
            log.archived_at = datetime.utcnow()

        try:
            db.session.commit()
            return len(logs_to_archive)
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error archiving logs: {e}")

    @staticmethod
    def get_logs_by_date_range(
        start_date: datetime,
        end_date: datetime,
        include_archived: bool = False
    ) -> List['AuditTrail']:
        """
        Retrieve audit logs within a date range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            include_archived: Whether to include archived logs

        Returns:
            List of audit logs within the date range
        """
        query = AuditTrail.query.filter(
            and_(
                AuditTrail.timestamp >= start_date,
                AuditTrail.timestamp <= end_date
            )
        )
        if not include_archived:
            query = query.filter_by(is_archived=False)
        return query.all()

    @staticmethod
    def get_logs_by_user(
        user_id: int,
        include_archived: bool = False
    ) -> List['AuditTrail']:
        """
        Retrieve audit logs for a specific user.

        Args:
            user_id: ID of the user
            include_archived: Whether to include archived logs

        Returns:
            List of audit logs for the user
        """
        query = AuditTrail.query.filter_by(user_id=user_id)
        if not include_archived:
            query = query.filter_by(is_archived=False)
        return query.all()

    @staticmethod
    def get_action_summary(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get summary statistics of audit actions.

        Args:
            start_date: Optional start date for the summary period
            end_date: Optional end date for the summary period

        Returns:
            Dictionary with action counts
        """
        query = db.session.query(
            AuditTrail.action,
            db.func.count(AuditTrail.id)
        ).group_by(AuditTrail.action)

        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)

        return {action.value: count for action, count in query.all()}

    @staticmethod
    def cleanup_archived_logs(days: int = 365) -> int:
        """
        Permanently delete archived logs older than specified days.

        Args:
            days: Number of days after which archived logs should be deleted

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logs_to_delete = AuditTrail.query.filter(
            and_(
                AuditTrail.is_archived.is_(True),
                AuditTrail.archived_at < cutoff_date
            )
        ).all()

        for log in logs_to_delete:
            db.session.delete(log)

        try:
            db.session.commit()
            return len(logs_to_delete)
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error cleaning up archived logs: {e}")
