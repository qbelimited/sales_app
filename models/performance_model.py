from extensions import db
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
from sqlalchemy import Index, and_, or_, func
from typing import Dict, List, Optional, Tuple, Union, TypedDict


class SalesTarget(db.Model):
    __tablename__ = 'sales_target'

    id = db.Column(db.Integer, primary_key=True)
    sales_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # Sales manager target
    target_sales_count = db.Column(db.Integer, nullable=False)  # Number of sales to achieve
    target_premium_amount = db.Column(db.Float, nullable=False)  # Total premium amount to sell
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Flexible target criteria
    target_criteria_type = db.Column(db.String(100), nullable=True, index=True)  # E.g., 'source_type', 'product_group'
    target_criteria_value = db.Column(db.String(100), nullable=True, index=True)  # E.g., 'paypoint', 'risk'

    # Optional fields to track target period
    period_start = db.Column(db.DateTime, nullable=True, index=True)
    period_end = db.Column(db.DateTime, nullable=True, index=True)

    # Relationships
    sales_manager = db.relationship('User', foreign_keys=[sales_manager_id], backref='sales_manager_targets')

    # Add composite indexes for common query patterns
    __table_args__ = (
        Index('idx_target_active_period', 'is_active', 'period_start', 'period_end'),
        Index('idx_target_criteria', 'target_criteria_type', 'target_criteria_value'),
        Index('idx_target_manager_period', 'sales_manager_id', 'period_start', 'period_end')
    )

    @validates('target_sales_count', 'target_premium_amount')
    def validate_target_values(self, key, value):
        """Ensure that target sales count and premium amount are non-negative."""
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    @validates('period_start', 'period_end')
    def validate_period_dates(self, key, value):
        """Validate that period dates are valid and in correct order."""
        if value:
            if not isinstance(value, datetime):
                raise ValueError(f"{key} must be a datetime object")
            if key == 'period_end' and self.period_start and value < self.period_start:
                raise ValueError("period_end cannot be before period_start")
        return value

    def check_activity_status(self):
        """Update the active status based on the current date."""
        now = datetime.utcnow()
        if self.period_start and self.period_end:
            self.is_active = self.period_start <= now <= self.period_end
        else:
            self.is_active = True  # If no period is set, consider the target always active

    def get_progress(self):
        """Calculate the progress towards the target."""
        try:
            from models.performance_model import SalesPerformance
            performance = SalesPerformance.query.filter_by(
                sales_manager_id=self.sales_manager_id,
                target_id=self.id,
                is_deleted=False
            ).first()

            if not performance:
                return {
                    'sales_count_progress': 0,
                    'premium_amount_progress': 0,
                    'sales_count_percentage': 0,
                    'premium_amount_percentage': 0
                }

            sales_count_progress = performance.actual_sales_count
            premium_amount_progress = performance.actual_premium_amount

            return {
                'sales_count_progress': sales_count_progress,
                'premium_amount_progress': premium_amount_progress,
                'sales_count_percentage': (sales_count_progress / self.target_sales_count) * 100 if self.target_sales_count > 0 else 0,
                'premium_amount_percentage': (premium_amount_progress / self.target_premium_amount) * 100 if self.target_premium_amount > 0 else 0
            }
        except Exception as e:
            raise ValueError(f"Error calculating target progress: {str(e)}")

    def serialize(self):
        """Return a serialized version of the SalesTarget object."""
        # Ensure the activity status is updated before serialization
        self.check_activity_status()
        progress = self.get_progress()
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
            'is_active': self.is_active,
            'progress': progress
        }

    @staticmethod
    def get_active_targets():
        """Fetch all active sales targets."""
        now = datetime.utcnow()
        return SalesTarget.query.filter(
            and_(
                or_(SalesTarget.period_start <= now, SalesTarget.period_start == None),
                or_(SalesTarget.period_end >= now, SalesTarget.period_end == None),
                SalesTarget.is_deleted == False
            )
        ).all()

    @staticmethod
    def create_monthly_targets(sales_manager_id, target_sales_count, target_premium_amount, period_start, period_end, target_criteria_type=None, target_criteria_value=None):
        """Create monthly targets if the period exceeds one month."""
        try:
            targets = []
            current_start = period_start

            # Validate period dates
            if period_end <= period_start:
                raise ValueError("period_end must be after period_start")

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

                current_start = next_month

            db.session.bulk_save_objects(targets)
            db.session.commit()
            return targets
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error creating monthly targets: {str(e)}")

    def get_performance_trend(self, days: int = 30) -> Dict:
        """Calculate performance trend over a specified period."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            performances = SalesPerformance.query.filter(
                and_(
                    SalesPerformance.sales_manager_id == self.sales_manager_id,
                    SalesPerformance.target_id == self.id,
                    SalesPerformance.performance_date.between(start_date, end_date),
                    SalesPerformance.is_deleted == False
                )
            ).order_by(SalesPerformance.performance_date).all()

            trend_data: Dict[str, List[Union[str, int, float]]] = {
                'dates': [],
                'sales_counts': [],
                'premium_amounts': [],
                'achievement_rates': []
            }

            for perf in performances:
                trend_data['dates'].append(perf.performance_date.isoformat())
                trend_data['sales_counts'].append(perf.actual_sales_count)
                trend_data['premium_amounts'].append(perf.actual_premium_amount)
                achievement = perf.calculate_achievement_rate()
                trend_data['achievement_rates'].append(
                    achievement['overall_rate'] if achievement else 0
                )

            return trend_data
        except Exception as e:
            raise ValueError(f"Error calculating performance trend: {str(e)}")

    def forecast_achievement(self) -> Dict:
        """Forecast target achievement based on current performance."""
        try:
            progress = self.get_progress()
            if not progress['sales_count_progress'] or not progress['premium_amount_progress']:
                return {
                    'forecast_sales_count': 0,
                    'forecast_premium_amount': 0,
                    'days_remaining': 0,
                    'achievement_forecast': 0
                }

            now = datetime.utcnow()
            if not self.period_end:
                return {
                    'forecast_sales_count': progress['sales_count_progress'],
                    'forecast_premium_amount': progress['premium_amount_progress'],
                    'days_remaining': 0,
                    'achievement_forecast': 0
                }

            days_elapsed = (now - self.period_start).days
            days_remaining = (self.period_end - now).days
            if days_elapsed <= 0 or days_remaining <= 0:
                return {
                    'forecast_sales_count': progress['sales_count_progress'],
                    'forecast_premium_amount': progress['premium_amount_progress'],
                    'days_remaining': days_remaining,
                    'achievement_forecast': 0
                }

            daily_sales_rate = progress['sales_count_progress'] / days_elapsed
            daily_premium_rate = progress['premium_amount_progress'] / days_elapsed

            forecast_sales = progress['sales_count_progress'] + (daily_sales_rate * days_remaining)
            forecast_premium = progress['premium_amount_progress'] + (daily_premium_rate * days_remaining)

            achievement_forecast = min(
                (forecast_sales / self.target_sales_count) * 100,
                (forecast_premium / self.target_premium_amount) * 100
            )

            return {
                'forecast_sales_count': forecast_sales,
                'forecast_premium_amount': forecast_premium,
                'days_remaining': days_remaining,
                'achievement_forecast': achievement_forecast
            }
        except Exception as e:
            raise ValueError(f"Error forecasting achievement: {str(e)}")

    def check_performance_alerts(self) -> List[Dict]:
        """Check for performance alerts based on targets."""
        alerts = []
        try:
            forecast = self.forecast_achievement()
            progress = self.get_progress()

            # Check if target is at risk
            if forecast['achievement_forecast'] < 80 and forecast['days_remaining'] > 0:
                alerts.append({
                    'type': 'target_risk',
                    'message': 'Target achievement is at risk',
                    'severity': 'warning',
                    'details': {
                        'current_achievement': progress['sales_count_percentage'],
                        'forecast_achievement': forecast['achievement_forecast']
                    }
                })

            # Check if target is significantly behind
            if progress['sales_count_percentage'] < 50 and forecast['days_remaining'] < 30:
                alerts.append({
                    'type': 'behind_schedule',
                    'message': 'Significantly behind target schedule',
                    'severity': 'critical',
                    'details': {
                        'current_achievement': progress['sales_count_percentage'],
                        'days_remaining': forecast['days_remaining']
                    }
                })

            return alerts
        except Exception as e:
            raise ValueError(f"Error checking performance alerts: {str(e)}")


class SalesPerformance(db.Model):
    __tablename__ = 'sales_performance'

    id = db.Column(db.Integer, primary_key=True)
    sales_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)  # Performance for sales managers
    actual_sales_count = db.Column(db.Integer, nullable=False)  # Actual number of sales made
    actual_premium_amount = db.Column(db.Float, nullable=False)  # Actual premium amount sold
    target_id = db.Column(db.Integer, db.ForeignKey('sales_target.id'), nullable=True)  # Link to the SalesTarget
    performance_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    # Flexible criteria fields
    criteria_type = db.Column(db.String(100), nullable=True, index=True)  # E.g., 'source_type', 'product_group'
    criteria_value = db.Column(db.String(100), nullable=True, index=True)  # E.g., 'paypoint', 'risk'
    criteria_met_count = db.Column(db.Integer, nullable=False, default=0)  # Number of sales that met the criteria

    # Relationships
    sales_manager = db.relationship('User', foreign_keys=[sales_manager_id], backref='sales_manager_performance')
    target = db.relationship('SalesTarget', backref='performance_entries')

    # Add composite indexes for common query patterns
    __table_args__ = (
        Index('idx_performance_manager_date', 'sales_manager_id', 'performance_date'),
        Index('idx_performance_criteria', 'criteria_type', 'criteria_value'),
        Index('idx_performance_target_date', 'target_id', 'performance_date')
    )

    @validates('actual_sales_count', 'actual_premium_amount', 'criteria_met_count')
    def validate_performance_values(self, key, value):
        """Ensure actual sales count, premium amount, and criteria met count are non-negative."""
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value

    @validates('performance_date')
    def validate_performance_date(self, key, value):
        """Validate that performance date is not in the future."""
        if value and value > datetime.utcnow():
            raise ValueError("Performance date cannot be in the future")
        return value

    def calculate_achievement_rate(self):
        """Calculate the achievement rate against the target."""
        try:
            if not self.target:
                return None

            sales_count_rate = (self.actual_sales_count / self.target.target_sales_count) * 100 if self.target.target_sales_count > 0 else 0
            premium_amount_rate = (self.actual_premium_amount / self.target.target_premium_amount) * 100 if self.target.target_premium_amount > 0 else 0

            return {
                'sales_count_rate': sales_count_rate,
                'premium_amount_rate': premium_amount_rate,
                'overall_rate': (sales_count_rate + premium_amount_rate) / 2
            }
        except Exception as e:
            raise ValueError(f"Error calculating achievement rate: {str(e)}")

    def serialize(self):
        """Return a serialized version of the SalesPerformance object."""
        achievement_rate = self.calculate_achievement_rate()
        return {
            'id': self.id,
            'sales_manager_id': self.sales_manager_id,
            'actual_sales_count': self.actual_sales_count,
            'actual_premium_amount': self.actual_premium_amount,
            'target_id': self.target_id,
            'performance_date': self.performance_date.isoformat(),
            'criteria_type': self.criteria_type,
            'criteria_value': self.criteria_value,
            'criteria_met_count': self.criteria_met_count,
            'achievement_rate': achievement_rate
        }

    @staticmethod
    def calculate_performance(sales_manager_id, start_date=None, end_date=None):
        """
        Calculate the overall performance for a sales manager within an optional date range.
        """
        try:
            query = SalesPerformance.query.filter_by(sales_manager_id=sales_manager_id, is_deleted=False)

            if start_date and end_date:
                query = query.filter(SalesPerformance.performance_date.between(start_date, end_date))

            total_sales_count = db.session.query(db.func.sum(SalesPerformance.actual_sales_count)).filter_by(
                sales_manager_id=sales_manager_id, is_deleted=False).scalar() or 0

            total_premium_amount = db.session.query(db.func.sum(SalesPerformance.actual_premium_amount)).filter_by(
                sales_manager_id=sales_manager_id, is_deleted=False).scalar() or 0

            return {
                'total_sales_count': total_sales_count,
                'total_premium_amount': total_premium_amount
            }
        except Exception as e:
            raise ValueError(f"Error calculating performance: {str(e)}")

    @staticmethod
    def get_performance_by_target(target_id):
        """
        Retrieve all performance entries for a specific target.
        """
        try:
            return SalesPerformance.query.filter_by(target_id=target_id, is_deleted=False).all()
        except Exception as e:
            raise ValueError(f"Error retrieving performance by target: {str(e)}")

    @staticmethod
    def get_performance_comparison(
        sales_manager_id: int,
        comparison_period: str = 'month'
    ) -> Dict:
        """Compare performance across different time periods."""
        try:
            now = datetime.utcnow()
            if comparison_period == 'month':
                start_date = now.replace(day=1)
                prev_start = (start_date - timedelta(days=1)).replace(day=1)
            elif comparison_period == 'quarter':
                quarter = (now.month - 1) // 3
                start_date = now.replace(month=quarter * 3 + 1, day=1)
                prev_start = (start_date - timedelta(days=1)).replace(day=1)
            else:
                start_date = now.replace(month=1, day=1)
                prev_start = start_date.replace(year=start_date.year - 1)

            current_period = SalesPerformance.query.filter(
                and_(
                    SalesPerformance.sales_manager_id == sales_manager_id,
                    SalesPerformance.performance_date >= start_date,
                    SalesPerformance.is_deleted == False
                )
            ).with_entities(
                func.sum(SalesPerformance.actual_sales_count).label('total_sales'),
                func.sum(SalesPerformance.actual_premium_amount).label('total_premium')
            ).first()

            previous_period = SalesPerformance.query.filter(
                and_(
                    SalesPerformance.sales_manager_id == sales_manager_id,
                    SalesPerformance.performance_date >= prev_start,
                    SalesPerformance.performance_date < start_date,
                    SalesPerformance.is_deleted == False
                )
            ).with_entities(
                func.sum(SalesPerformance.actual_sales_count).label('total_sales'),
                func.sum(SalesPerformance.actual_premium_amount).label('total_premium')
            ).first()

            return {
                'current_period': {
                    'sales_count': current_period.total_sales or 0,
                    'premium_amount': current_period.total_premium or 0
                },
                'previous_period': {
                    'sales_count': previous_period.total_sales or 0,
                    'premium_amount': previous_period.total_premium or 0
                },
                'comparison': {
                    'sales_count_change': (
                        ((current_period.total_sales or 0) - (previous_period.total_sales or 0)) /
                        (previous_period.total_sales or 1) * 100
                    ),
                    'premium_amount_change': (
                        ((current_period.total_premium or 0) - (previous_period.total_premium or 0)) /
                        (previous_period.total_premium or 1) * 100
                    )
                }
            }
        except Exception as e:
            raise ValueError(f"Error comparing performance: {str(e)}")

    @staticmethod
    def get_team_performance(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """Get aggregated performance for all sales managers."""
        try:
            query = SalesPerformance.query.filter(
                SalesPerformance.is_deleted == False
            )

            if start_date and end_date:
                query = query.filter(
                    SalesPerformance.performance_date.between(start_date, end_date)
                )

            team_performance = query.with_entities(
                SalesPerformance.sales_manager_id,
                func.sum(SalesPerformance.actual_sales_count).label('total_sales'),
                func.sum(SalesPerformance.actual_premium_amount).label('total_premium'),
                func.count(SalesPerformance.id).label('performance_count')
            ).group_by(SalesPerformance.sales_manager_id).all()

            return [{
                'sales_manager_id': perf.sales_manager_id,
                'total_sales': perf.total_sales or 0,
                'total_premium': perf.total_premium or 0,
                'performance_count': perf.performance_count
            } for perf in team_performance]
        except Exception as e:
            raise ValueError(f"Error getting team performance: {str(e)}")


class TrendData(TypedDict):
    dates: List[str]
    sales_counts: List[int]
    premium_amounts: List[float]
    achievement_rates: List[float]
