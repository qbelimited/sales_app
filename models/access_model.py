from app import db
from sqlalchemy.orm import validates
from models.user_model import Role

class Access(db.Model):
    __tablename__ = 'access'

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    can_create = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_view_logs = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_view_audit_trail = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # Relationship to Role
    role = db.relationship('Role', backref=db.backref('access_rules', lazy=True))

    def serialize(self):
        """Serialize access rule for API responses."""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'can_create': self.can_create,
            'can_update': self.can_update,
            'can_delete': self.can_delete,
            'can_view_logs': self.can_view_logs,
            'can_manage_users': self.can_manage_users,
            'can_view_audit_trail': self.can_view_audit_trail,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @validates('can_create', 'can_update', 'can_delete', 'can_view_logs', 'can_manage_users', 'can_view_audit_trail')
    def validate_boolean_fields(self, key, value):
        """Ensure that the boolean fields are valid."""
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be a boolean value")
        return value

    def save(self):
        """Save access rule to the database."""
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error saving access rule: {str(e)}")

    def delete(self, soft_delete=True):
        """Delete or soft delete the access rule."""
        try:
            if soft_delete:
                self.is_deleted = True
            else:
                db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error deleting access rule: {str(e)}")

    @staticmethod
    def get_active_access_rules():
        """Retrieve all non-deleted access rules."""
        return Access.query.filter_by(is_deleted=False).all()
