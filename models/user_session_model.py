from app import db
from datetime import datetime
import ipaddress


class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    is_active = db.Column(db.Boolean, default=True)

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
        self.is_active = False
        if not self.logout_time:
            self.logout_time = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def validate_ip(ip):
        """Validate IP address format (IPv4 or IPv6)."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
