from extensions import db
from datetime import datetime
from sqlalchemy.orm import validates
from typing import Optional, Dict, List, Any
from enum import Enum
from sqlalchemy import func


class ExecutiveStatus(Enum):
    """Status of a sales executive."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ON_LEAVE = 'on_leave'
    TERMINATED = 'terminated'


# Association table for many-to-many relationship between sales executives and branches
sales_executive_branches = db.Table(
    'sales_executive_branches',
    db.Column(
        'sales_executive_id',
        db.Integer,
        db.ForeignKey('sales_executive.id'),
        primary_key=True
    ),
    db.Column(
        'branch_id',
        db.Integer,
        db.ForeignKey('branch.id'),
        primary_key=True
    )
)


class SalesExecutive(db.Model):
    """Model representing a sales executive in the system."""
    __tablename__ = 'sales_executive'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    manager_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False,
        index=True
    )
    phone_number = db.Column(
        db.String(10),
        nullable=True,
        unique=True,
        index=True
    )
    email = db.Column(db.String(100), nullable=True, unique=True, index=True)
    status = db.Column(
        db.String(20),
        nullable=False,
        default=ExecutiveStatus.ACTIVE.value,
        index=True
    )
    target_sales_count = db.Column(db.Integer, nullable=True)
    target_premium_amount = db.Column(db.Float, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    manager = db.relationship('User', backref='sales_executives')
    branches = db.relationship(
        'Branch',
        secondary=sales_executive_branches,
        backref=db.backref('sales_executives', lazy='dynamic')
    )

    @validates('phone_number')
    def validate_phone_number(self, _, phone_number):
        """Validate phone number format."""
        if phone_number and (
            len(phone_number) != 10 or not phone_number.isdigit()
        ):
            raise ValueError("Phone number must be 10 digits and numeric")
        return phone_number

    @validates('email')
    def validate_email(self, _, email):
        """Validate email format."""
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email

    @validates('status')
    def validate_status(self, _, status):
        """Validate executive status."""
        try:
            ExecutiveStatus(status)
        except ValueError:
            raise ValueError(f"Invalid status: {status}")
        return status

    def serialize(self) -> Dict:
        """Serialize the sales executive data."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'manager_id': self.manager_id,
            'phone_number': self.phone_number,
            'email': self.email,
            'status': self.status,
            'target_sales_count': self.target_sales_count,
            'target_premium_amount': self.target_premium_amount,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': (
                self.updated_at.isoformat() if self.updated_at else None
            ),
            'last_active_at': (
                self.last_active_at.isoformat() if self.last_active_at else None
            ),
            'branches': [branch.serialize() for branch in self.branches]
        }

    def update_last_active(self) -> None:
        """Update the last active timestamp."""
        self.last_active_at = datetime.utcnow()
        db.session.commit()

    def get_performance_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for the sales executive."""
        try:
            from models.sales_model import Sale

            query = Sale.query.filter_by(
                sales_executive_id=self.id,
                is_deleted=False
            )

            if start_date:
                query = query.filter(Sale.created_at >= start_date)
            if end_date:
                query = query.filter(Sale.created_at <= end_date)

            total_sales = query.count()
            total_premium = db.session.query(
                func.sum(Sale.amount)
            ).filter_by(
                sales_executive_id=self.id,
                is_deleted=False
            ).scalar() or 0

            sales_percentage = (
                (total_sales / self.target_sales_count * 100)
                if self.target_sales_count else 0
            )
            premium_percentage = (
                (total_premium / self.target_premium_amount * 100)
                if self.target_premium_amount else 0
            )

            return {
                'total_sales': total_sales,
                'total_premium': total_premium,
                'target_achievement': {
                    'sales_count': sales_percentage,
                    'premium_amount': premium_percentage
                }
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}

    @staticmethod
    def get_active_sales_executives(
        page: int = 1,
        per_page: int = 10,
        status: Optional[str] = None
    ) -> List['SalesExecutive']:
        """Get active sales executives with optional status filter."""
        try:
            query = SalesExecutive.query.filter_by(is_deleted=False)
            if status:
                query = query.filter_by(status=status)
            return query.paginate(page=page, per_page=per_page).items
        except Exception as e:
            logger.error(f"Error fetching active sales executives: {e}")
            raise ValueError(f"Error fetching active sales executives: {e}")

    @staticmethod
    def get_sales_executives_by_manager(
        manager_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> List['SalesExecutive']:
        """Get sales executives under a specific manager."""
        try:
            return SalesExecutive.query.filter_by(
                manager_id=manager_id,
                is_deleted=False
            ).paginate(page=page, per_page=per_page).items
        except Exception as e:
            logger.error(f"Error fetching sales executives by manager: {e}")
            raise ValueError(f"Error fetching sales executives by manager: {e}")

    @staticmethod
    def get_sales_executives_by_branch(
        branch_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> List['SalesExecutive']:
        """Get sales executives for a specific branch."""
        try:
            return SalesExecutive.query.join(
                SalesExecutive.branches
            ).filter_by(
                id=branch_id
            ).filter(
                SalesExecutive.is_deleted.is_(False)
            ).paginate(page=page, per_page=per_page).items
        except Exception as e:
            logger.error(f"Error fetching sales executives by branch: {e}")
            raise ValueError(f"Error fetching sales executives by branch: {e}")

    @staticmethod
    def soft_delete_sales_executive(executive_id: int) -> bool:
        """Soft delete a sales executive."""
        try:
            executive = SalesExecutive.query.filter_by(
                id=executive_id,
                is_deleted=False
            ).first()
            if executive:
                executive.is_deleted = True
                executive.status = ExecutiveStatus.TERMINATED.value
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error soft deleting sales executive: {e}")
            raise ValueError(f"Error soft deleting sales executive: {e}")
