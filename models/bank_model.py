from app import db
from datetime import datetime
from sqlalchemy.orm import validates
from typing import List, Dict, Any, Optional
from sqlalchemy import and_


class Bank(db.Model):
    """
    Model representing a bank in the system.
    Each bank can have multiple branches and supports soft deletion.
    """
    __tablename__ = 'bank'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    bank_branches = db.relationship(
        'BankBranch',
        backref='bank',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate bank name."""
        if not name or name.strip() == "":
            raise ValueError("Bank name cannot be empty")
        if len(name.strip()) > 100:
            raise ValueError("Bank name cannot exceed 100 characters")
        return name.strip()

    def serialize(self) -> Dict[str, Any]:
        """Serialize bank data for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bank_branches': [
                branch.serialize() for branch in self.bank_branches
                if not branch.is_deleted
            ]
        }

    @staticmethod
    def get_active_banks(page: int = 1, per_page: int = 10000) -> List['Bank']:
        """
        Retrieve paginated list of active banks.

        Args:
            page: Page number for pagination
            per_page: Number of items per page

        Returns:
            List of active banks

        Raises:
            ValueError: If fetching fails
        """
        try:
            return Bank.query.filter_by(is_deleted=False).paginate(
                page=page,
                per_page=per_page
            ).items
        except Exception as e:
            raise ValueError(f"Error fetching active banks: {e}")

    @staticmethod
    def search_banks(query: str) -> List['Bank']:
        """
        Search banks by name.

        Args:
            query: Search query string

        Returns:
            List of matching banks
        """
        return Bank.query.filter(
            and_(
                Bank.is_deleted.is_(False),
                Bank.name.ilike(f'%{query}%')
            )
        ).all()

    @staticmethod
    def get_bank_summary() -> Dict[str, int]:
        """
        Get summary statistics of banks and branches.

        Returns:
            Dictionary with bank and branch counts
        """
        active_banks = Bank.query.filter_by(is_deleted=False).count()
        active_branches = BankBranch.query.filter_by(is_deleted=False).count()
        return {
            'active_banks': active_banks,
            'active_branches': active_branches
        }


class BankBranch(db.Model):
    """
    Model representing a bank branch.
    Each branch belongs to a bank and supports soft deletion.
    """
    __tablename__ = 'bank_branch'
    __table_args__ = (
        db.UniqueConstraint('name', 'bank_id', name='uq_branch_name_bank'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    bank_id = db.Column(
        db.Integer,
        db.ForeignKey('bank.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    sort_code = db.Column(db.String(50), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate branch name."""
        if not name or name.strip() == "":
            raise ValueError("Branch name cannot be empty")
        if len(name.strip()) > 100:
            raise ValueError("Branch name cannot exceed 100 characters")
        return name.strip()

    @validates('sort_code')
    def validate_sort_code(
        self,
        key: str,
        sort_code: Optional[str]
    ) -> Optional[str]:
        """Validate sort code format."""
        if sort_code and not sort_code.strip().isdigit():
            raise ValueError("Sort code must contain only digits")
        return sort_code.strip() if sort_code else None

    def serialize(self) -> Dict[str, Any]:
        """Serialize branch data for API responses."""
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
    def get_active_branches(page: int = 1, per_page: int = 10) -> List['BankBranch']:
        """
        Retrieve paginated list of active bank branches.

        Args:
            page: Page number for pagination
            per_page: Number of items per page

        Returns:
            List of active branches

        Raises:
            ValueError: If fetching fails
        """
        try:
            return BankBranch.query.filter_by(is_deleted=False).paginate(
                page=page,
                per_page=per_page
            ).items
        except Exception as e:
            raise ValueError(f"Error fetching active bank branches: {e}")

    @staticmethod
    def get_branches_by_bank(bank_id: int) -> List['BankBranch']:
        """
        Retrieve all active branches for a specific bank.

        Args:
            bank_id: ID of the bank

        Returns:
            List of active branches for the bank
        """
        return BankBranch.query.filter(
            and_(
                BankBranch.bank_id == bank_id,
                BankBranch.is_deleted.is_(False)
            )
        ).all()
