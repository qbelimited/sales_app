from app import db
from datetime import datetime


# Association table for many-to-many relationship between sales executives and branches
user_branches = db.Table('user_branches',
    db.Column('sales_executive_id', db.Integer, db.ForeignKey('sales_executive.id'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id'), primary_key=True)
)


class SalesExecutive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    manager = db.relationship('User', backref='sales_executives')
    branch = db.relationship('Branch', backref='sales_executives')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'manager_id': self.manager_id,
            'branch_id': self.branch_id,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
