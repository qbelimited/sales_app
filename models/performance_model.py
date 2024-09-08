from app import db
from datetime import datetime


class SalesTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_executive_id = db.Column(db.Integer, db.ForeignKey('sales_executive.id'), nullable=True, index=True)  # Sales executive target
    sales_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # Sales manager target
    target_sales_count = db.Column(db.Integer, nullable=False)  # The number of sales to achieve
    target_premium_amount = db.Column(db.Float, nullable=False)  # The total premium amount to sell
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sales_executive = db.relationship('SalesExecutive', backref='sales_targets')
    sales_manager = db.relationship('User', foreign_keys=[sales_manager_id], backref='sales_manager_targets')

    def serialize(self):
        return {
            'id': self.id,
            'sales_executive_id': self.sales_executive_id,
            'sales_manager_id': self.sales_manager_id,
            'target_sales_count': self.target_sales_count,
            'target_premium_amount': self.target_premium_amount,
            'created_at': self.created_at.isoformat()
        }


class SalesPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_executive_id = db.Column(db.Integer, db.ForeignKey('sales_executive.id'), nullable=True, index=True)  # Performance for sales executives
    sales_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # Performance for sales managers
    actual_sales_count = db.Column(db.Integer, nullable=False)  # Actual number of sales made
    actual_premium_amount = db.Column(db.Float, nullable=False)  # Actual premium amount sold
    target_id = db.Column(db.Integer, db.ForeignKey('sales_target.id'), nullable=True)  # Link to the SalesTarget
    performance_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sales_executive = db.relationship('SalesExecutive', backref='sales_performance')
    sales_manager = db.relationship('User', foreign_keys=[sales_manager_id], backref='sales_manager_performance')
    target = db.relationship('SalesTarget', backref='performance_entries')

    def serialize(self):
        return {
            'id': self.id,
            'sales_executive_id': self.sales_executive_id,
            'sales_manager_id': self.sales_manager_id,
            'actual_sales_count': self.actual_sales_count,
            'actual_premium_amount': self.actual_premium_amount,
            'target_id': self.target_id,
            'performance_date': self.performance_date.isoformat()
        }
