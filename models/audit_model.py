from app import db
from datetime import datetime
import zlib
from sqlalchemy.types import TypeDecorator, LargeBinary


# CompressedText class for compressing old_value and new_value fields
class CompressedText(TypeDecorator):
    impl = LargeBinary

    def process_bind_param(self, value, _):
        if value is None:
            return None
        return zlib.compress(value.encode('utf-8'))

    def process_result_value(self, value, _):
        if value is None:
            return None
        return zlib.decompress(value).decode('utf-8')


# AuditTrail model to store audit logs
class AuditTrail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.Integer, nullable=False)
    old_value = db.Column(CompressedText, nullable=True)  # Store compressed old value
    new_value = db.Column(CompressedText, nullable=True)  # Store compressed new value
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref='audit_trails')

    __table_args__ = (
        db.Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }
