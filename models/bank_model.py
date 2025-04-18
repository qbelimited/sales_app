from extensions import db
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
    code = db.Column(db.String(20), nullable=True, unique=True)  # Bank code (e.g., SWIFT, BIC)
    website = db.Column(db.String(200), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    bank_type = db.Column(db.String(50), nullable=True)  # Commercial, Development, etc.
    bank_branches = db.relationship(
        'BankBranch',
        backref='bank',
        lazy='selectin',
        cascade='all, delete-orphan'
    )
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Define account number length requirements for different banks
    ACCOUNT_LENGTH_REQUIREMENTS = {
        'UNITED BANK FOR AFRICA': 14,
        'ZENITH': 10,
        'ABSA': 10,
        'SOCIETE GENERAL': [12, 13]
    }

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Validate bank name."""
        if not name or name.strip() == "":
            raise ValueError("Bank name cannot be empty")
        if len(name.strip()) > 100:
            raise ValueError("Bank name cannot exceed 100 characters")
        return name.strip()

    @validates('code')
    def validate_code(self, key: str, code: Optional[str]) -> Optional[str]:
        """Validate bank code."""
        if code and not code.strip().isalnum():
            raise ValueError("Bank code must contain only alphanumeric characters")
        return code.strip() if code else None

    @validates('contact_phone')
    def validate_contact_phone(self, key: str, phone: Optional[str]) -> Optional[str]:
        """Validate contact phone number."""
        if phone and (len(phone.strip()) != 10 or not phone.strip().isdigit()):
            raise ValueError("Contact phone number must be exactly 10 digits")
        return phone.strip() if phone else None

    @validates('contact_email')
    def validate_contact_email(self, key: str, email: Optional[str]) -> Optional[str]:
        """Validate contact email."""
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email.strip() if email else None

    def validate_account_number(self, account_number: str) -> bool:
        """
        Validate bank account number based on bank-specific requirements.

        Args:
            account_number: The account number to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not account_number or not account_number.strip().isdigit():
            return False

        length = len(account_number.strip())
        bank_name_lower = self.name.lower()

        # Check account number requirements based on the bank name
        for keyword, required_length in self.ACCOUNT_LENGTH_REQUIREMENTS.items():
            if keyword.lower() in bank_name_lower:
                if isinstance(required_length, list):
                    return length in required_length
                return length == required_length

        # Default validation for other banks
        return length in [10, 12, 13, 14, 16]

    def serialize(self) -> Dict[str, Any]:
        """Serialize bank data for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'website': self.website,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'logo_url': self.logo_url,
            'bank_type': self.bank_type,
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
    def search_banks(query: str, bank_type: Optional[str] = None) -> List['Bank']:
        """
        Search banks by name and optionally by type.

        Args:
            query: Search query string
            bank_type: Optional bank type filter

        Returns:
            List of matching banks
        """
        search_query = Bank.query.filter(
            and_(
                Bank.is_deleted.is_(False),
                Bank.name.ilike(f'%{query}%')
            )
        )

        if bank_type:
            search_query = search_query.filter(Bank.bank_type == bank_type)

        return search_query.all()

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
    code = db.Column(db.String(20), nullable=True, unique=True)  # Branch code/identifier
    bank_id = db.Column(
        db.Integer,
        db.ForeignKey('bank.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    sort_code = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
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

    @validates('code')
    def validate_code(self, key: str, code: Optional[str]) -> Optional[str]:
        """Validate branch code."""
        if code and not code.strip().isalnum():
            raise ValueError("Branch code must contain only alphanumeric characters")
        return code.strip() if code else None

    @validates('sort_code')
    def validate_sort_code(self, key: str, sort_code: Optional[str]) -> Optional[str]:
        """Validate sort code format."""
        if sort_code and not sort_code.strip().isdigit():
            raise ValueError("Sort code must contain only digits")
        return sort_code.strip() if sort_code else None

    @validates('contact_phone')
    def validate_contact_phone(self, key: str, phone: Optional[str]) -> Optional[str]:
        """Validate contact phone number."""
        if phone and (len(phone.strip()) != 10 or not phone.strip().isdigit()):
            raise ValueError("Contact phone number must be exactly 10 digits")
        return phone.strip() if phone else None

    @validates('contact_email')
    def validate_contact_email(self, key: str, email: Optional[str]) -> Optional[str]:
        """Validate contact email."""
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email.strip() if email else None

    @validates('latitude', 'longitude')
    def validate_coordinates(self, key: str, value: Optional[float]) -> Optional[float]:
        """Validate geographical coordinates."""
        if value is not None:
            if key == 'latitude' and (value < -90 or value > 90):
                raise ValueError("Latitude must be between -90 and 90")
            elif key == 'longitude' and (value < -180 or value > 180):
                raise ValueError("Longitude must be between -180 and 180")
        return value

    def serialize(self) -> Dict[str, Any]:
        """Serialize branch data for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'bank_id': self.bank_id,
            'sort_code': self.sort_code,
            'address': self.address,
            'city': self.city,
            'region': self.region,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
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

    @staticmethod
    def search_branches(query: str, bank_id: Optional[int] = None, city: Optional[str] = None) -> List['BankBranch']:
        """
        Search branches by name, optionally filtered by bank and city.

        Args:
            query: Search query string
            bank_id: Optional bank ID filter
            city: Optional city filter

        Returns:
            List of matching branches
        """
        search_query = BankBranch.query.filter(
            and_(
                BankBranch.is_deleted.is_(False),
                BankBranch.name.ilike(f'%{query}%')
            )
        )

        if bank_id:
            search_query = search_query.filter(BankBranch.bank_id == bank_id)
        if city:
            search_query = search_query.filter(BankBranch.city.ilike(f'%{city}%'))

        return search_query.all()
