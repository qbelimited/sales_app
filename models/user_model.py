from extensions import db
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
import re
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import json
from flask import request
import logging
from functools import lru_cache
from models.audit_model import AuditTrail

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserStatus(Enum):
    """User account status."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    LOCKED = 'locked'


# Association table for many-to-many relationship between users and branches
user_branches = db.Table('user_branches',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id'), primary_key=True)
)


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Text, nullable=True)  # JSON string of permissions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # New fields for role hierarchy and tracking
    parent_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, inactive, deprecated
    usage_count = db.Column(db.Integer, default=0)  # Track how many users have this role
    last_assigned_at = db.Column(db.DateTime, nullable=True)
    validation_rules = db.Column(db.Text, nullable=True)  # JSON string of validation rules

    # Relationship for role hierarchy
    parent = db.relationship('Role', remote_side=[id], backref='children')

    # Relationship with users
    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_deleted': self.is_deleted,
            'permissions': json.loads(self.permissions) if self.permissions else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'parent_id': self.parent_id,
            'status': self.status,
            'usage_count': self.usage_count,
            'last_assigned_at': self.last_assigned_at.isoformat() if self.last_assigned_at else None,
            'validation_rules': json.loads(self.validation_rules) if self.validation_rules else {}
        }

    def increment_usage(self):
        """Increment the usage count and update last assigned timestamp."""
        self.usage_count += 1
        self.last_assigned_at = datetime.utcnow()
        db.session.commit()

    def decrement_usage(self):
        """Decrement the usage count."""
        if self.usage_count > 0:
            self.usage_count -= 1
            db.session.commit()

    def get_hierarchy(self):
        """Get the complete role hierarchy including parent and children."""
        hierarchy = {
            'role': self.serialize(),
            'parent': self.parent.serialize() if self.parent else None,
            'children': [child.serialize() for child in self.children]
        }
        return hierarchy

    def validate_rules(self, user_data):
        """Validate user data against role validation rules."""
        if not self.validation_rules:
            return True, None

        try:
            rules = json.loads(self.validation_rules)
            for field, rule in rules.items():
                if field in user_data:
                    if not self._validate_rule(rule, user_data[field]):
                        return False, f"Validation failed for {field}"
            return True, None
        except json.JSONDecodeError:
            return False, "Invalid validation rules"

    def _validate_rule(self, rule, value):
        """Validate a single rule against a value."""
        if rule.get('type') == 'regex':
            return bool(re.match(rule['pattern'], str(value)))
        elif rule.get('type') == 'range':
            return rule['min'] <= value <= rule['max']
        elif rule.get('type') == 'enum':
            return value in rule['values']
        return True

    def get_usage_analytics(self):
        """Get analytics about role usage."""
        return {
            'total_users': self.usage_count,
            'last_assigned': self.last_assigned_at.isoformat() if self.last_assigned_at else None,
            'active_users': self.users.filter_by(is_active=True).count(),
            'inactive_users': self.users.filter_by(is_active=False).count()
        }

    def update_status(self, new_status):
        """Update the role status with validation."""
        valid_statuses = ['active', 'inactive', 'deprecated']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")

        if new_status == 'deprecated' and self.usage_count > 0:
            raise ValueError("Cannot deprecate a role that is still in use")

        self.status = new_status
        db.session.commit()

    @staticmethod
    def get_role_hierarchy(role_id=None):
        """Get the complete role hierarchy starting from a specific role or all roles."""
        if role_id:
            role = Role.query.get(role_id)
            if not role:
                return None
            return role.get_hierarchy()

        # Get all root roles (roles without parents)
        root_roles = Role.query.filter_by(parent_id=None, is_deleted=False).all()
        return [role.get_hierarchy() for role in root_roles]


def validate_status_transition(current_status, new_status):
    """Validate if a status transition is allowed."""
    valid_transitions = {
        UserStatus.ACTIVE.value: [UserStatus.INACTIVE.value, UserStatus.SUSPENDED.value, UserStatus.LOCKED.value],
        UserStatus.INACTIVE.value: [UserStatus.ACTIVE.value],
        UserStatus.SUSPENDED.value: [UserStatus.ACTIVE.value],
        UserStatus.LOCKED.value: [UserStatus.ACTIVE.value]
    }
    if new_status not in valid_transitions.get(current_status, []):
        raise ValueError(f"Invalid status transition from {current_status} to {new_status}")


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Security Features
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    last_password_change = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, nullable=True)
    inactivity_timeout = db.Column(db.Integer, default=30)  # minutes

    # Activity Tracking
    last_login = db.Column(db.DateTime, nullable=True)
    login_history = db.Column(db.Text, nullable=True)  # JSON array of logins
    current_device = db.Column(db.String(255), nullable=True)
    device_history = db.Column(db.Text, nullable=True)  # JSON array of devices
    status = db.Column(db.String(20), default=UserStatus.ACTIVE.value)

    # Relationships
    role = db.relationship('Role', back_populates='users')
    branches = db.relationship('Branch', secondary=user_branches, backref=db.backref('users', lazy='selectin'))

    @validates('email')
    def validate_email(self, _, email):
        if not email or email.strip() == "":
            raise ValueError("Invalid email address")
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format")
        return email

    @validates('status')
    def validate_status(self, _, status):
        try:
            UserStatus(status)
            return status
        except ValueError:
            raise ValueError(f"Invalid status. Must be one of: {[s.value for s in UserStatus]}")

    # Password hashing
    @property
    def password(self):
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, password):
        if password is None or password.strip() == "":
            password = "Password"  # Set default password
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.utcnow()
        self.failed_login_attempts = 0
        self.account_locked_until = None

    def check_password(self, password):
        """Check password and handle failed attempts."""
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            raise ValueError("Account is locked. Please try again later.")

        if check_password_hash(self.password_hash, password):
            self.failed_login_attempts = 0
            self.account_locked_until = None
            return True

        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        return False

    def update_login_history(self, device_info=None):
        """Update login history with current login information."""
        try:
            history = json.loads(self.login_history) if self.login_history else []
            history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'device_info': device_info or self.current_device,
                'ip_address': request.remote_addr if hasattr(request, 'remote_addr') else None
            })
            # Keep only last 10 logins
            self.login_history = json.dumps(history[-10:])
            self.last_login = datetime.utcnow()
            self.current_device = device_info
            self.last_activity = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating login history: {e}")
            db.session.rollback()

    def update_device_history(self, device_info):
        """Update device history with new device information."""
        try:
            history = json.loads(self.device_history) if self.device_history else []
            if device_info not in history:
                history.append({
                    'device_info': device_info,
                    'first_seen': datetime.utcnow().isoformat(),
                    'last_seen': datetime.utcnow().isoformat()
                })
            else:
                for device in history:
                    if device['device_info'] == device_info:
                        device['last_seen'] = datetime.utcnow().isoformat()
                        break
            self.device_history = json.dumps(history)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error updating device history: {e}")
            db.session.rollback()

    def check_inactivity_timeout(self):
        """Check if user session has timed out due to inactivity."""
        if not self.last_activity:
            return True
        timeout = timedelta(minutes=self.inactivity_timeout)
        return datetime.utcnow() - self.last_activity > timeout

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        db.session.commit()

    def serialize(self):
        """Serialize user data safely."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.serialize() if self.role else None,
            'branches': [branch.serialize() for branch in self.branches],
            'is_active': self.is_active,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'status': self.status,
            'last_password_change': self.last_password_change.isoformat() if self.last_password_change else None,
            'account_locked_until': self.account_locked_until.isoformat() if self.account_locked_until else None
        }

    @staticmethod
    def get_active_users():
        """Retrieve list of active users."""
        return User.query.filter_by(is_deleted=False, is_active=True).all()

    def check_permission(self, permission):
        """Check if user has a specific permission."""
        from models.access_model import Access  # Lazy import to avoid circular dependency

        if not self.role_id:
            return False

        # Get permissions from Access model
        access_rules = Access.get_role_permissions(self.role_id)
        if not access_rules:
            return False

        # Check if permission exists and is granted
        for _, perms in access_rules.items():
            if permission in perms and perms[permission]:
                return True

        return False

    def get_effective_permissions(self):
        """Get all effective permissions for the user."""
        from models.access_model import Access  # Lazy import to avoid circular dependency

        if not self.role_id:
            return {}

        return Access.get_role_permissions(self.role_id)

    @classmethod
    @lru_cache(maxsize=100)
    def get_by_id(cls, user_id):
        """Get user by ID with caching."""
        return cls.query.get(user_id)

    @classmethod
    @lru_cache(maxsize=100)
    def get_by_email(cls, email):
        """Get user by email with caching."""
        return cls.query.filter_by(email=email, is_deleted=False).first()

    def update_status(self, new_status):
        """Update user status."""
        try:
            validate_status_transition(self.status, new_status)
            self.status = new_status
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user status: {str(e)}")
            db.session.rollback()
            return False

    def update_password(self, new_password):
        """Update user password."""
        try:
            self.password = new_password
            self.last_password_change = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating password: {str(e)}")
            db.session.rollback()
            return False

    def get_activity_metrics(self, days=30):
        """Get user activity metrics for the last N days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        try:
            login_history = json.loads(self.login_history) if self.login_history else []
            recent_logins = [
                login for login in login_history
                if datetime.fromisoformat(login['timestamp']) >= start_date
            ]

            return {
                'total_logins': len(recent_logins),
                'unique_devices': len(set(login.get('device_info', '') for login in recent_logins)),
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'status_changes': self.get_status_changes(start_date, end_date)
            }
        except Exception as e:
            logger.error(f"Error getting activity metrics: {str(e)}")
            return None

    def get_status_changes(self, start_date, end_date):
        """Get user status changes within a date range."""
        try:
            audit_trails = AuditTrail.query.filter(
                AuditTrail.user_id == self.id,
                AuditTrail.action == 'STATUS_CHANGE',
                AuditTrail.created_at.between(start_date, end_date)
            ).all()

            return [{
                'old_status': trail.details.get('old_status'),
                'new_status': trail.details.get('new_status'),
                'timestamp': trail.created_at.isoformat()
            } for trail in audit_trails]
        except Exception as e:
            logger.error(f"Error getting status changes: {str(e)}")
            return []

    def invalidate_cache(self):
        """Invalidate cached user data."""
        self.get_by_id.cache_clear()
        self.get_by_email.cache_clear()

    def __repr__(self):
        return f'<User {self.email}>'
