from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Branch(db.Model):
    __tablename__ = 'branch'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    ghpost_gps = db.Column(db.String(11), nullable=True, unique=True)  # Consider making GPS unique
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships with User and SalesExecutive models
    users = db.relationship('User', backref='branch', lazy='joined')  # Consider using 'joined' for performance
    sales_executives = db.relationship('SalesExecutive', backref='branch', lazy='joined')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'region': self.region,
            'ghpost_gps': self.ghpost_gps,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'users': [user.id for user in self.users],
            'sales_executives': [sales_executive.id for sales_executive in self.sales_executives]
        }

    @staticmethod
    def get_active_branches():
        """Static method to get non-deleted branches."""
        try:
            return Branch.query.filter_by(is_deleted=False).all()
        except Exception as e:
            raise ValueError(f"Error fetching active branches: {e}")
