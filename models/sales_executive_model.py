from app import db
from datetime import datetime
from sqlalchemy.orm import validates

# Association table for many-to-many relationship between sales executives and branches
sales_executive_branches = db.Table('sales_executive_branches',
    db.Column('sales_executive_id', db.Integer, db.ForeignKey('sales_executive.id'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id'), primary_key=True)
)

class SalesExecutive(db.Model):
    __tablename__ = 'sales_executive'  # Explicitly set the table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    phone_number = db.Column(db.String(10), nullable=True, unique=True, index=True)  # Optionally ensure uniqueness
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    manager = db.relationship('User', backref='sales_executives')
    branches = db.relationship('Branch', secondary=sales_executive_branches, backref=db.backref('sales_executives', lazy='dynamic'))

    @validates('phone_number')
    def validate_phone_number(self, key, phone_number):
        if phone_number and len(phone_number) != 10:
            raise ValueError("Phone number must be 10 digits")
        return phone_number

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'manager_id': self.manager_id,
            'phone_number': self.phone_number,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'branches': [branch.id for branch in self.branches]  # Serialize branch IDs associated with this sales executive
        }

    @staticmethod
    def get_active_sales_executives(page=1, per_page=10):
        """Retrieve paginated list of active sales executives."""
        try:
            return SalesExecutive.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active sales executives: {e}")
