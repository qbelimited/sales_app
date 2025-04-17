from app import db, logger
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
import re
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum
import json
from flask import request


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

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_deleted': self.is_deleted,
            'permissions': json.loads(self.permissions) if self.permissions else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


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
    role = db.relationship('Role', backref='users')
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
        if not self.role or not self.role.permissions:
            return False
        permissions = json.loads(self.role.permissions)
        return permission in permissions

    def get_effective_permissions(self):
        """Get all effective permissions for the user."""
        if not self.role or not self.role.permissions:
            return set()
        return set(json.loads(self.role.permissions))

