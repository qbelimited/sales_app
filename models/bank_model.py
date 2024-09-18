from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Bank(db.Model):
    __tablename__ = 'bank'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    bank_branches = db.relationship('BankBranch', backref='bank', lazy='selectin')  # Optimized lazy loading
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Validation for bank name
    @validates('name')
    def validate_name(self, key, name):
        if not name or name.strip() == "":
            raise ValueError("Bank name cannot be empty")
        return name

    # Serialization of bank model
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bank_branches': [branch.serialize() for branch in self.bank_branches if not branch.is_deleted]
        }

    @staticmethod
    def get_active_banks(page=1, per_page=10000):
        """Retrieve paginated list of active banks."""
        try:
            return Bank.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active banks: {e}")


class BankBranch(db.Model):
    __tablename__ = 'bank_branch'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False, index=True)
    sort_code = db.Column(db.String(50), nullable=True)  # Optional sort code field
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Validation for bank branch name
    @validates('name')
    def validate_name(self, key, name):
        if not name or name.strip() == "":
            raise ValueError("Branch name cannot be empty")
        return name

    # Serialization of bank branch model
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'bank_id': self.bank_id,
            'sort_code': self.sort_code,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_branches(page=1, per_page=10):
        """Retrieve paginated list of active bank branches."""
        try:
            return BankBranch.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active bank branches: {e}")
