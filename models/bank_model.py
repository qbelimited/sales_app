from app import db
from datetime import datetime

class Bank(db.Model):
    __tablename__ = 'bank'  # Explicitly set the table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    bank_branches = db.relationship('BankBranch', backref='bank', lazy=True)  # Update to reflect the new class name
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bank_branches': [bank_branch.serialize() for bank_branch in self.bank_branches]
        }

class BankBranch(db.Model):
    __tablename__ = 'bank_branch'  # Explicitly set the table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=False, index=True)
    sort_code = db.Column(db.String(255), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'bank_id': self.bank_id,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
