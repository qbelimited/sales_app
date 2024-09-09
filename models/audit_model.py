from app import db
from datetime import datetime
from enum import Enum


# Enum for Audit actions
class AuditAction(Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    REVOKE_REFRESH_TOKEN = 'REVOKE_REFRESH_TOKEN'
    ACCESS = 'ACCESS'  # Add other actions as needed


# AuditTrail model to store audit logs
class AuditTrail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    action = db.Column(db.Enum(AuditAction), nullable=False)  # Use Enum for action
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.Integer, nullable=True)
    old_value = db.Column(db.String(255), nullable=True)
    new_value = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref='audit_trails')

    __table_args__ = (
        db.Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action.value,  # Serialize enum as its value
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
