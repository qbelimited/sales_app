from app import db
from datetime import datetime
from sqlalchemy.orm import validates

# Association table for many-to-many relationship between users and branches
user_branches = db.Table('user_branches',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'role'  # Explicitly set the table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

class User(db.Model):
    __tablename__ = 'user'  # Explicitly set the table name

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False, index=True)
    branches = db.relationship('Branch', secondary=user_branches, backref=db.backref('users', lazy=True))
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    microsoft_id = db.Column(db.String(255), unique=True, nullable=True, index=True)  # Microsoft 365 unique ID for the user

    role = db.relationship('Role', backref='users')

    @validates('email')
    def validate_email(self, key, email):
        if '@' not in email or '.' not in email.split('@')[-1]:
            raise ValueError("Invalid email address")
        return email

    def serialize(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role_id': self.role_id,
            'branches': [branch.serialize() for branch in self.branches],
            'is_active': self.is_active,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'microsoft_id': self.microsoft_id
        }
