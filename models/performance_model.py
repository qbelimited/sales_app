from app import db
from datetime import datetime, timedelta
from sqlalchemy.orm import validates

class SalesTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # Sales manager target
    target_sales_count = db.Column(db.Integer, nullable=False)  # Number of sales to achieve
    target_premium_amount = db.Column(db.Float, nullable=False)  # Total premium amount to sell
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Flexible target criteria
    target_criteria_type = db.Column(db.String(100), nullable=True)  # E.g., 'source_type', 'product_group'
    target_criteria_value = db.Column(db.String(100), nullable=True)  # E.g., 'paypoint', 'risk'

    # Optional fields to track target period
    period_start = db.Column(db.DateTime, nullable=True)
    period_end = db.Column(db.DateTime, nullable=True)

    # Relationships
    sales_manager = db.relationship('User', foreign_keys=[sales_manager_id], backref='sales_manager_targets')

    @validates('target_sales_count', 'target_premium_amount')
    def validate_target_values(self, key, value):
        """Ensure that target sales count and premium amount are non-negative."""
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    def check_activity_status(self):
        """Update the active status based on the current date."""
        now = datetime.utcnow()
        if self.period_start and self.period_end:
            self.is_active = self.period_start <= now <= self.period_end
        else:
            self.is_active = True  # If no period is set, consider the target always active

    def serialize(self):
        """Return a serialized version of the SalesTarget object."""
        # Ensure the activity status is updated before serialization
        self.check_activity_status()
        return {
            'id': self.id,
            'sales_manager_id': self.sales_manager_id,
            'target_sales_count': self.target_sales_count,
            'target_premium_amount': self.target_premium_amount,
            'target_criteria_type': self.target_criteria_type,
            'target_criteria_value': self.target_criteria_value,
            'created_at': self.created_at.isoformat(),
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'is_active': self.is_active
        }

    @staticmethod
    def get_active_targets():
        """Fetch all active sales targets."""
        now = datetime.utcnow()
        return SalesTarget.query.filter(
            db.or_(SalesTarget.period_start <= now, SalesTarget.period_start == None),
            db.or_(SalesTarget.period_end >= now, SalesTarget.period_end == None)
        ).all()

    @staticmethod
    def create_monthly_targets(sales_manager_id, target_sales_count, target_premium_amount, period_start, period_end, target_criteria_type=None, target_criteria_value=None):
        """Create monthly targets if the period exceeds one month."""
        targets = []
        current_start = period_start

        # Calculate the number of months in the period
        total_months = ((period_end.year - period_start.year) * 12 + (period_end.month - period_start.month)) + 1

        # Calculate monthly targets
        monthly_sales_count = target_sales_count // total_months
        monthly_premium_amount = target_premium_amount / total_months

        while current_start < period_end:
            next_month = (current_start + timedelta(days=30)).replace(day=1)
            current_end = min(next_month, period_end)

            monthly_target = SalesTarget(
                sales_manager_id=sales_manager_id,
                target_sales_count=monthly_sales_count,
                target_premium_amount=monthly_premium_amount,
                period_start=current_start,
                period_end=current_end,
                target_criteria_type=target_criteria_type,
                target_criteria_value=target_criteria_value
            )
            targets.append(monthly_target)

            # Move to the next month
            current_start = next_month

        db.session.bulk_save_objects(targets)
        db.session.commit()

class SalesPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # Performance for sales managers
    actual_sales_count = db.Column(db.Integer, nullable=False)  # Actual number of sales made
    actual_premium_amount = db.Column(db.Float, nullable=False)  # Actual premium amount sold
    target_id = db.Column(db.Integer, db.ForeignKey('sales_target.id'), nullable=True)  # Link to the SalesTarget
    performance_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    # Flexible criteria fields
    criteria_type = db.Column(db.String(100), nullable=True)  # E.g., 'source_type', 'product_group'
    criteria_value = db.Column(db.String(100), nullable=True)  # E.g., 'paypoint', 'risk'
    criteria_met_count = db.Column(db.Integer, nullable=False, default=0)  # Number of sales that met the criteria

    # Relationships
    sales_manager = db.relationship('User', foreign_keys=[sales_manager_id], backref='sales_manager_performance')
    target = db.relationship('SalesTarget', backref='performance_entries')

    @validates('actual_sales_count', 'actual_premium_amount', 'criteria_met_count')
    def validate_performance_values(self, key, value):
        """Ensure actual sales count, premium amount, and criteria met count are non-negative."""
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    def serialize(self):
        """Return a serialized version of the SalesPerformance object."""
        return {
            'id': self.id,
            'sales_manager_id': self.sales_manager_id,
            'actual_sales_count': self.actual_sales_count,
            'actual_premium_amount': self.actual_premium_amount,
            'target_id': self.target_id,
            'performance_date': self.performance_date.isoformat(),
            'criteria_type': self.criteria_type,
            'criteria_value': self.criteria_value,
            'criteria_met_count': self.criteria_met_count
        }

    @staticmethod
    def calculate_performance(sales_manager_id, start_date=None, end_date=None):
        """
        Calculate the overall performance for a sales manager within an optional date range.
        """
        query = SalesPerformance.query.filter_by(sales_manager_id=sales_manager_id)

        if start_date and end_date:
            query = query.filter(SalesPerformance.performance_date.between(start_date, end_date))

        total_sales_count = db.session.query(db.func.sum(SalesPerformance.actual_sales_count)).filter_by(
            sales_manager_id=sales_manager_id).scalar() or 0

        total_premium_amount = db.session.query(db.func.sum(SalesPerformance.actual_premium_amount)).filter_by(
            sales_manager_id=sales_manager_id).scalar() or 0

        return {
            'total_sales_count': total_sales_count,
            'total_premium_amount': total_premium_amount
        }

    @staticmethod
    def get_performance_by_target(target_id):
        """
        Retrieve all performance entries for a specific target.
        """
        return SalesPerformance.query.filter_by(target_id=target_id).all()
