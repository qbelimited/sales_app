from app import db
from datetime import datetime
from sqlalchemy.orm import validates
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_


class Branch(db.Model):
    """
    Model representing a branch location in the system.
    Supports soft deletion and includes geographical information.
    """
    __tablename__ = 'branch'
    __table_args__ = (
        db.Index('idx_branch_region', 'region'),
        db.Index('idx_branch_city', 'city'),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    ghpost_gps = db.Column(db.String(11), nullable=True, unique=True)  # Ensure uniqueness for GPS
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('name', 'ghpost_gps', 'address', 'city', 'region')
    def validate_fields(
        self,
        key: str,
        value: Optional[str]
    ) -> Optional[str]:
        """
        Validate branch fields.

        Args:
            key: Field name being validated
            value: Value to validate

        Returns:
            Validated and formatted value

        Raises:
            ValueError: If validation fails
        """
        if value is None:
            return None

        value = value.strip()

        if key == 'name':
            if not value:
                raise ValueError("Branch name cannot be empty")
            if len(value) > 100:
                raise ValueError("Branch name cannot exceed 100 characters")

        elif key == 'ghpost_gps':
            if value and len(value) != 11:
                raise ValueError("GhPost GPS must be exactly 11 characters")

        elif key == 'address':
            if value and len(value) > 255:
                raise ValueError("Address cannot exceed 255 characters")

        elif key in ('city', 'region'):
            if value and len(value) > 100:
                raise ValueError(f"{key.capitalize()} cannot exceed 100 characters")

        return value

    def serialize(self) -> Dict[str, Any]:
        """Serialize branch data for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'ghpost_gps': self.ghpost_gps,
            'address': self.address,
            'city': self.city,
            'region': self.region,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @staticmethod
    def get_active_branches(
        page: int = 1,
        per_page: int = 10
    ) -> List['Branch']:
        """
        Retrieve paginated list of active branches.

        Args:
            page: Page number for pagination
            per_page: Number of items per page

        Returns:
            List of active branches

        Raises:
            ValueError: If fetching fails
        """
        try:
            return Branch.query.filter_by(is_deleted=False).paginate(
                page=page,
                per_page=per_page
            ).items
        except Exception as e:
            raise ValueError(f"Error fetching active branches: {e}")

    @staticmethod
    def search_branches(
        query: str,
        region: Optional[str] = None
    ) -> List['Branch']:
        """
        Search branches by name or GPS code, optionally filtered by region.

        Args:
            query: Search query string
            region: Optional region filter

        Returns:
            List of matching branches
        """
        filters = [
            Branch.is_deleted.is_(False),
            or_(
                Branch.name.ilike(f'%{query}%'),
                Branch.ghpost_gps.ilike(f'%{query}%')
            )
        ]

        if region:
            filters.append(Branch.region.ilike(f'%{region}%'))

        return Branch.query.filter(and_(*filters)).all()

    @staticmethod
    def get_branches_by_region(region: str) -> List['Branch']:
        """
        Retrieve all active branches in a specific region.

        Args:
            region: Region name

        Returns:
            List of branches in the region
        """
        return Branch.query.filter(
            and_(
                Branch.is_deleted.is_(False),
                Branch.region.ilike(f'%{region}%')
            )
        ).all()

    @staticmethod
    def get_branch_summary() -> Dict[str, int]:
        """
        Get summary statistics of branches.

        Returns:
            Dictionary with branch counts by region
        """
        from sqlalchemy import func
        return {
            'total_branches': Branch.query.filter_by(is_deleted=False).count(),
            'branches_by_region': dict(
                Branch.query.with_entities(
                    Branch.region,
                    func.count(Branch.id)
                ).filter_by(is_deleted=False)
                .group_by(Branch.region)
                .all()
            )
        }

