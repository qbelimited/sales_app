from app import db
from sqlalchemy.orm import validates
from models.user_model import Role
from sqlalchemy import UniqueConstraint


class Access(db.Model):
    """
    Access model representing permission rules for different roles in the system.
    Each role can have one set of access rules that define what actions they can
    perform.
    """
    __tablename__ = 'access'
    __table_args__ = (
        UniqueConstraint('role_id', name='uq_access_role_id'),
        db.Index('idx_access_role_id', 'role_id'),
        db.Index('idx_access_is_deleted', 'is_deleted'),
    )

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(
        db.Integer,
        db.ForeignKey('role.id', ondelete='CASCADE'),
        nullable=False
    )
    can_create = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_view_logs = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_view_audit_trail = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

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

    @validates('role_id')
    def validate_role_id(self, key, value):
        """Validate that the role_id exists in the Role table."""
        if not Role.query.get(value):
            raise ValueError(f"Role with id {value} does not exist")
        return value

    @validates('can_create', 'can_update', 'can_delete', 'can_view_logs',
               'can_manage_users', 'can_view_audit_trail')
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

    def has_permission(self, permission_type):
        """Check if this access rule has a specific permission.

        Args:
            permission_type (str): The type of permission to check
                (e.g., 'can_create', 'can_update')

        Returns:
            bool: True if the permission is granted, False otherwise
        """
        return getattr(self, permission_type, False)

    @staticmethod
    def get_active_access_rules():
        """Retrieve all non-deleted access rules."""
        return Access.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_access_by_role(role_id):
        """Retrieve access rules for a specific role.

        Args:
            role_id (int): The ID of the role to get access rules for

        Returns:
            Access: The access rules for the specified role, or None if not found
        """
        return Access.query.filter_by(role_id=role_id, is_deleted=False).first()
