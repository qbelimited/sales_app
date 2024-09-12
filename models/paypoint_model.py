from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Paypoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True, unique=True)  # Ensure uniqueness
    location = db.Column(db.String(255), nullable=True)  # Optional location
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('name')
    def validate_name(self, _, name):
        if not name or len(name) > 100:
            raise ValueError("Paypoint name must be provided and less than 100 characters")
        return name

    @validates('location')
    def validate_location(self, _, location):
        if location and len(location) > 255:
            raise ValueError("Location must be less than 255 characters")
        return location

    def serialize(self):
        """Return a serialized version of the Paypoint."""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_paypoints(page=1, per_page=10):
        """Retrieve a paginated list of active (non-deleted) paypoints."""
        try:
            paginated_paypoints = Paypoint.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page, error_out=False)
            return {
                'items': [paypoint.serialize() for paypoint in paginated_paypoints.items],
                'total': paginated_paypoints.total,
                'pages': paginated_paypoints.pages,
                'current_page': paginated_paypoints.page
            }
        except Exception as e:
            raise ValueError(f"Error fetching active paypoints: {str(e)}")

    @staticmethod
    def get_deleted_paypoints(page=1, per_page=10):
        """Retrieve a paginated list of soft-deleted paypoints."""
        try:
            paginated_paypoints = Paypoint.query.filter_by(is_deleted=True).paginate(page=page, per_page=per_page, error_out=False)
            return {
                'items': [paypoint.serialize() for paypoint in paginated_paypoints.items],
                'total': paginated_paypoints.total,
                'pages': paginated_paypoints.pages,
                'current_page': paginated_paypoints.page
            }
        except Exception as e:
            raise ValueError(f"Error fetching deleted paypoints: {str(e)}")

    def soft_delete(self):
        """Soft-delete the paypoint (set `is_deleted` to True)."""
        try:
            self.is_deleted = True
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error soft-deleting paypoint: {str(e)}")

    def restore(self):
        """Restore a soft-deleted paypoint (set `is_deleted` to False)."""
        try:
            self.is_deleted = False
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error restoring paypoint: {str(e)}")

    @staticmethod
    def permanently_delete(paypoint_id):
        """Permanently delete a paypoint from the database."""
        try:
            paypoint = Paypoint.query.get(paypoint_id)
            if paypoint:
                db.session.delete(paypoint)
                db.session.commit()
            else:
                raise ValueError(f"Paypoint with ID {paypoint_id} not found")
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error permanently deleting paypoint: {str(e)}")
