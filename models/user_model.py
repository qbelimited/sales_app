from app import db
from datetime import datetime
from sqlalchemy.orm import validates
import re
from werkzeug.security import generate_password_hash, check_password_hash

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

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_deleted': self.is_deleted
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

    # Role relationship
    role = db.relationship('Role', backref='users')
    branches = db.relationship('Branch', secondary=user_branches, backref=db.backref('users', lazy='selectin'))

    # Validation for email format and uniqueness
    @validates('email')
    def validate_email(self, _, email):
        if not email or email.strip() == "":
            raise ValueError("Invalid email address")
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email):
            raise ValueError("Invalid email format")
        return email

    # Password hashing
    @property
    def password(self):
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, password):
        if not password or password.strip() == "":
            raise ValueError("Password cannot be empty")
        self.password_hash = generate_password_hash(password)

    # Method to check password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Method to set password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Serialize method to return user data safely
    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role.serialize() if self.role else None,
            'branches': [branch.serialize() for branch in self.branches],  # Include related branches
            'is_active': self.is_active,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_users():
        """Retrieve list of active users."""
        return User.query.filter_by(is_deleted=False, is_active=True).all()

