from app import db
from models.user_model import Role

class Access(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    can_create = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_view_logs = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_view_audit_trail = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationship to Role
    role = db.relationship('Role', backref='role_access_rules')

    def serialize(self):
        return {
            'id': self.id,
            'role_id': self.role_id,
            'can_create': self.can_create,
            'can_update': self.can_update,
            'can_delete': self.can_delete,
            'can_view_logs': self.can_view_logs,
            'can_manage_users': self.can_manage_users,
            'can_view_audit_trail': self.can_view_audit_trail,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
