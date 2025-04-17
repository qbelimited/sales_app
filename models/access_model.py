from app import (
    db,
    cache
)
from sqlalchemy.orm import validates
from models.user_model import Role
from sqlalchemy import UniqueConstraint
import json
import logging
from typing import (
    Dict,
    List,
    Optional
)
from datetime import datetime

logger = logging.getLogger(__name__)


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
        db.ForeignKey('role.id'),
        nullable=False,
        index=True
    )
    resource = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )
    can_create = db.Column(db.Boolean, default=False)
    can_read = db.Column(db.Boolean, default=False)
    can_update = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_export = db.Column(db.Boolean, default=False)
    can_import = db.Column(db.Boolean, default=False)
    can_approve = db.Column(db.Boolean, default=False)
    can_reject = db.Column(db.Boolean, default=False)
    can_audit = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(
        db.Boolean,
        default=False,
        index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # New fields for enhanced RBAC
    conditions = db.Column(
        db.Text,
        nullable=True
    )  # JSON string of conditions
    scope = db.Column(
        db.String(50),
        nullable=True
    )  # global, branch, department
    priority = db.Column(
        db.Integer,
        default=0
    )  # Higher priority overrides lower
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(
        db.Boolean,
        default=True,
        index=True
    )

    # Relationship
    role = db.relationship('Role', backref='access_rules')

    def __init__(self, **kwargs):
        super(Access, self).__init__(**kwargs)
        self._validate_conditions()

    def _validate_conditions(self):
        """Validate the conditions JSON string."""
        if self.conditions:
            try:
                conditions = json.loads(self.conditions)
                if not isinstance(conditions, dict):
                    raise ValueError(
                        "Conditions must be a JSON object"
                    )
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in conditions")

    @validates('conditions')
    def validate_conditions(self, key, value):
        if value:
            try:
                conditions = json.loads(value)
                if not isinstance(conditions, dict):
                    raise ValueError(
                        "Conditions must be a JSON object"
                    )
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in conditions")
        return value

    @validates('scope')
    def validate_scope(self, key, value):
        valid_scopes = ['global', 'branch', 'department']
        if value and value not in valid_scopes:
            raise ValueError(
                f"Scope must be one of: {', '.join(valid_scopes)}"
            )
        return value

    @classmethod
    @cache.memoize(timeout=300)  # Cache for 5 minutes
    def get_role_permissions(cls, role_id: int) -> Dict:
        """Get all permissions for a role, including inherited permissions."""
        role = db.session.query(Role).get(role_id)
        if not role:
            return {}

        # Get direct permissions
        permissions = {}
        access_rules = (
            cls.query
            .filter_by(
                role_id=role_id,
                is_deleted=False,
                is_active=True
            )
            .all()
        )

        for rule in access_rules:
            if rule.resource not in permissions:
                permissions[rule.resource] = {}
            permissions[rule.resource].update({
                'create': rule.can_create,
                'read': rule.can_read,
                'update': rule.can_update,
                'delete': rule.can_delete,
                'export': rule.can_export,
                'import': rule.can_import,
                'approve': rule.can_approve,
                'reject': rule.can_reject,
                'audit': rule.can_audit,
                'conditions': (
                    json.loads(rule.conditions)
                    if rule.conditions else {}
                ),
                'scope': rule.scope,
                'priority': rule.priority
            })

        # Get inherited permissions from parent roles
        if role.parent_id:
            parent_permissions = cls.get_role_permissions(role.parent_id)
            for resource, resource_perms in parent_permissions.items():
                if resource not in permissions:
                    permissions[resource] = resource_perms
                else:
                    # Merge permissions, keeping higher priority rules
                    for perm, value in resource_perms.items():
                        if perm not in permissions[resource]:
                            permissions[resource][perm] = value
                        elif (
                            'priority' in resource_perms and
                            resource_perms['priority'] >
                            permissions[resource].get('priority', 0)
                        ):
                            permissions[resource][perm] = value

        return permissions

    @classmethod
    def check_permission(
        cls,
        role_id: int,
        resource: str,
        action: str,
        context: Optional[Dict] = None
    ) -> bool:
        """Check if a role has permission to perform an action on a resource."""
        permissions = cls.get_role_permissions(role_id)
        if resource not in permissions:
            return False

        resource_perms = permissions[resource]
        if action not in resource_perms:
            return False

        # Check conditions if present
        if 'conditions' in resource_perms and context:
            conditions = resource_perms['conditions']
            for key, value in conditions.items():
                if key not in context or context[key] != value:
                    return False

        return resource_perms[action]

    @classmethod
    def get_effective_permissions(cls, role_id: int) -> Dict:
        """Get all effective permissions for a role, including inherited ones."""
        return cls.get_role_permissions(role_id)

    @classmethod
    def clear_permission_cache(cls, role_id: int):
        """Clear the permission cache for a role."""
        cache.delete_memoized(cls.get_role_permissions, role_id)

    def to_dict(self):
        """Convert access rule to dictionary."""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'resource': self.resource,
            'can_create': self.can_create,
            'can_read': self.can_read,
            'can_update': self.can_update,
            'can_delete': self.can_delete,
            'can_export': self.can_export,
            'can_import': self.can_import,
            'can_approve': self.can_approve,
            'can_reject': self.can_reject,
            'can_audit': self.can_audit,
            'is_deleted': self.is_deleted,
            'created_at': (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            'updated_at': (
                self.updated_at.isoformat()
                if self.updated_at else None
            ),
            'conditions': (
                json.loads(self.conditions)
                if self.conditions else {}
            ),
            'scope': self.scope,
            'priority': self.priority,
            'expires_at': (
                self.expires_at.isoformat()
                if self.expires_at else None
            ),
            'is_active': self.is_active
        }

    @classmethod
    def get_active_rules(cls, role_id: int) -> List['Access']:
        """Get all active access rules for a role."""
        return cls.query.filter_by(
            role_id=role_id,
            is_deleted=False,
            is_active=True
        ).all()

    @classmethod
    def get_expired_rules(cls) -> List['Access']:
        """Get all expired access rules."""
        return (
            cls.query
            .filter(
                cls.expires_at < datetime.utcnow(),
                cls.is_active
            )
            .all()
        )

    def is_expired(self) -> bool:
        """Check if the access rule has expired."""
        return (
            self.expires_at is not None and
            self.expires_at < datetime.utcnow()
        )

    def deactivate(self):
        """Deactivate an access rule."""
        self.is_active = False
        self.clear_permission_cache(self.role_id)
        db.session.commit()

    def activate(self):
        """Activate an access rule."""
        self.is_active = True
        self.clear_permission_cache(self.role_id)
        db.session.commit()

    @classmethod
    def cleanup_expired_rules(cls):
        """Deactivate all expired access rules."""
        expired_rules = cls.get_expired_rules()
        for rule in expired_rules:
            rule.deactivate()
        return len(expired_rules)

    def serialize(self):
        """Serialize access rule for API responses."""
        return {
            'id': self.id,
            'role_id': self.role_id,
            'resource': self.resource,
            'can_create': self.can_create,
            'can_read': self.can_read,
            'can_update': self.can_update,
            'can_delete': self.can_delete,
            'can_export': self.can_export,
            'can_import': self.can_import,
            'can_approve': self.can_approve,
            'can_reject': self.can_reject,
            'can_audit': self.can_audit,
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

    @validates('can_create', 'can_update', 'can_delete', 'can_read', 'can_export',
               'can_import', 'can_approve', 'can_reject', 'can_audit')
    def validate_boolean_fields(self, key, value):
        """Ensure that the boolean fields are valid."""
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be a boolean value")
        return value

    def save(self):
        """Save access rule to the database and sync to role."""
        try:
            db.session.add(self)
            db.session.commit()
            self.sync_to_role_permissions()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error saving access rule: {str(e)}")

    def delete(self, soft_delete=True):
        """Delete or soft delete the access rule and update role permissions."""
        try:
            if soft_delete:
                self.is_deleted = True
            else:
                db.session.delete(self)
            db.session.commit()
            self.sync_to_role_permissions()
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

    @staticmethod
    def get_all_permissions():
        """Get a list of all available permission types."""
        return [
            'can_create',
            'can_read',
            'can_update',
            'can_delete',
            'can_export',
            'can_import',
            'can_approve',
            'can_reject',
            'can_audit'
        ]

    def has_any_permission(self, permission_types):
        """Check if this access rule has any of the specified permissions.

        Args:
            permission_types (list): List of permission types to check

        Returns:
            bool: True if any of the permissions are granted, False otherwise
        """
        return any(
            getattr(self, permission, False)
            for permission in permission_types
        )

    def has_all_permissions(self, permission_types):
        """Check if this access rule has all of the specified permissions.

        Args:
            permission_types (list): List of permission types to check

        Returns:
            bool: True if all permissions are granted, False otherwise
        """
        return all(
            getattr(self, permission, False)
            for permission in permission_types
        )

    def sync_to_role_permissions(self):
        """Sync the access permissions to the role's permissions field."""
        try:
            role = self.role
            if not role:
                return

            permissions = {
                'can_create': self.can_create,
                'can_read': self.can_read,
                'can_update': self.can_update,
                'can_delete': self.can_delete,
                'can_export': self.can_export,
                'can_import': self.can_import,
                'can_approve': self.can_approve,
                'can_reject': self.can_reject,
                'can_audit': self.can_audit
            }

            role.permissions = json.dumps(permissions)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing permissions to role: {str(e)}")
            raise
