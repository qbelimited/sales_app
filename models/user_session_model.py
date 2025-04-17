from app import db, logger
from datetime import datetime, timedelta
import ipaddress
from sqlalchemy.orm import validates
from utils import get_client_ip
import secrets
import os
from typing import Optional, List
from sqlalchemy import Index, and_, func
from models.retention_model import RetentionPolicy, DataType

# Configure logging
logger = logging.getLogger(__name__)


class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(
            minutes=int(os.getenv('SESSION_EXPIRY_MINUTES', 45))
        )
    )
    ip_address = db.Column(db.String(45), default=lambda: get_client_ip())
    is_active = db.Column(db.Boolean, default=True, index=True)
    session_token = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        default=lambda: secrets.token_hex(32)
    )
    token_expires_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(
            minutes=int(os.getenv('TOKEN_EXPIRY_MINUTES', 15))
        )
    )
    user_agent = db.Column(db.String(255), nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    device_fingerprint = db.Column(db.String(64), nullable=True)
    activity_count = db.Column(db.Integer, default=0)
    suspicious_activity = db.Column(db.Boolean, default=False)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    device_info = db.Column(db.String(255), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete flag

    # Add indexes for performance
    __table_args__ = (
        Index('idx_user_session_active', 'user_id', 'is_active'),
        Index('idx_session_token', 'session_token'),
    )

    user = db.relationship('User', backref='sessions')

    def serialize(self):
        """Serialize the session to JSON-friendly format."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'is_deleted': self.is_deleted
        }

    @staticmethod
    def get_active_sessions(user_id: Optional[int] = None) -> List['UserSession']:
        """Retrieve all active sessions or for a specific user if provided.
        Automatically expire sessions."""
        now = datetime.utcnow()

        query = UserSession.query.filter(
            UserSession.is_active,
            UserSession.expires_at > now
        )

        if user_id:
            query = query.filter(UserSession.user_id == user_id)

        sessions = query.all()

        for session in sessions:
            if session.expires_at <= now:
                session.end_session()

        db.session.commit()
        return sessions

    def end_session(self) -> None:
        """Ends the session by setting is_active to False and adding the logout time."""
        try:
            self.is_active = False
            if not self.logout_time:
                self.logout_time = datetime.utcnow()
            db.session.commit()
            logger.info(f"Session {self.id} ended successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error ending session {self.id}: {str(e)}")
            raise ValueError(f"Error ending session: {e}")

    def update_last_activity(self) -> None:
        """Updates the last activity timestamp for the session."""
        try:
            self.last_activity = datetime.utcnow()
            self.activity_count += 1
            self.check_suspicious_activity()
            db.session.commit()
            logger.debug(f"Updated activity for session {self.id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating session activity {self.id}: {str(e)}")
            raise ValueError(f"Error updating session activity: {e}")

    def rotate_token(self) -> str:
        """Rotates the session token for enhanced security."""
        try:
            self.session_token = secrets.token_hex(32)
            self.token_expires_at = datetime.utcnow() + timedelta(
                minutes=int(os.getenv('TOKEN_EXPIRY_MINUTES', 15))
            )
            db.session.commit()
            logger.info(f"Token rotated for session {self.id}")
            return self.session_token
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error rotating token for session {self.id}: {str(e)}")
            raise ValueError(f"Error rotating token: {e}")

    def check_suspicious_activity(self) -> None:
        """Checks for suspicious activity patterns."""
        if self.activity_count > int(os.getenv('MAX_ACTIVITY_COUNT', 100)):
            self.suspicious_activity = True
            logger.warning(f"Suspicious activity detected in session {self.id}")

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format (IPv4 or IPv6)."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @validates('ip_address')
    def validate_ip_address(self, _, ip: str) -> str:
        """Validate IP address upon session creation or update."""
        if not self.validate_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")
        return ip

    def get_session_duration(self) -> Optional[float]:
        """Returns the session duration in seconds, or None if session is still active."""
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds()
        return None

    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions based on retention policy."""
        try:
            # Get retention policy for sessions
            policy = RetentionPolicy.get_policy(DataType.USER_SESSIONS.value)
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)

            # Get sessions to delete
            sessions_to_delete = UserSession.query.filter(
                and_(
                    UserSession.expires_at < cutoff_date,
                    UserSession.is_deleted == False
                )
            ).all()

            # Archive sessions if required by policy
            if policy.archive_before_delete:
                for session in sessions_to_delete:
                    # Archive session data
                    archived_data = ArchivedData(
                        data_type=DataType.USER_SESSIONS.value,
                        original_id=session.id,
                        retention_policy_id=policy.id
                    )
                    archived_data.compress_data(session.serialize())
                    db.session.add(archived_data)

            # Mark sessions as deleted
            for session in sessions_to_delete:
                session.is_deleted = True

            db.session.commit()
            return len(sessions_to_delete)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up expired sessions: {e}")
            raise ValueError(f"Error cleaning up expired sessions: {e}")

    @staticmethod
    def get_active_sessions():
        """Get all non-deleted active sessions."""
        return UserSession.query.filter(
            and_(
                UserSession.is_active == True,
                UserSession.is_deleted == False
            )
        ).all()

    @staticmethod
    def get_expired_sessions():
        """Get all expired but not deleted sessions."""
        return UserSession.query.filter(
            and_(
                UserSession.expires_at < datetime.utcnow(),
                UserSession.is_deleted == False
            )
        ).all()

    def is_valid(self) -> bool:
        """Check if the session is still valid."""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.expires_at > now and
            self.token_expires_at > now and
            not self.suspicious_activity
        )

    @staticmethod
    def bulk_update_sessions(session_ids: List[int], **kwargs) -> int:
        """Bulk update multiple sessions."""
        try:
            updated = UserSession.query.filter(
                UserSession.id.in_(session_ids)
            ).update(kwargs, synchronize_session=False)
            db.session.commit()
            logger.info(f"Bulk updated {updated} sessions")
            return updated
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in bulk update: {str(e)}")
            raise ValueError(f"Error in bulk update: {e}")
