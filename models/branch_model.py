from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Branch(db.Model):
    __tablename__ = 'branch'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    ghpost_gps = db.Column(db.String(11), nullable=True, unique=True)  # Ensure uniqueness for GPS
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Validation for branch name and ghpost_gps
    @validates('name', 'ghpost_gps')
    def validate_fields(self, key, value):
        if key == 'name' and (not value or value.strip() == ""):
            raise ValueError("Branch name cannot be empty")
        if key == 'ghpost_gps' and value and len(value) != 11:
            raise ValueError("GhPost GPS must be exactly 11 characters")
        return value

    # Serialize the branch data for API responses
    def serialize(self):
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
    def get_active_branches(page=1, per_page=10):
        """Static method to retrieve paginated list of active (non-deleted) branches."""
        try:
            return Branch.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active branches: {e}")

