from app import db
from datetime import datetime

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
