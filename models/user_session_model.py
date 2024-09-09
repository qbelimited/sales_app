from app import db
from datetime import datetime
import ipaddress
from sqlalchemy.orm import validates


class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    is_active = db.Column(db.Boolean, default=True, index=True)

    user = db.relationship('User', backref='sessions')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'login_time': self.login_time.isoformat(),
            'logout_time': self.logout_time.isoformat() if self.logout_time else None,
            'ip_address': self.ip_address,
            'is_active': self.is_active
        }

    @staticmethod
    def get_active_sessions(user_id=None):
        """Retrieve all active sessions or for a specific user if provided."""
        if user_id:
            return UserSession.query.filter_by(user_id=user_id, is_active=True).all()
        return UserSession.query.filter_by(is_active=True).all()

    def end_session(self):
        """Ends the session by setting is_active to False and adding the logout time."""
        try:
            self.is_active = False
            if not self.logout_time:
                self.logout_time = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error ending session: {e}")

    @staticmethod
    def validate_ip(ip):
        """Validate IP address format (IPv4 or IPv6)."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @validates('ip_address')
    def validate_ip_address(self, key, ip):
        """Validate IP address upon session creation or update."""
        if not self.validate_ip(ip):
            raise ValueError(f"Invalid IP address: {ip}")
        return ip

    def get_session_duration(self):
        """Returns the session duration in seconds, or None if session is still active."""
        if self.logout_time:
            return (self.logout_time - self.login_time).total_seconds()
        return None  # Active session
