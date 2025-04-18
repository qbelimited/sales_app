from extensions import db
from datetime import datetime
from sqlalchemy.orm import validates
from sqlalchemy import Index, UniqueConstraint
from models.sales_model import Sale
import json

class Paypoint(db.Model):
    __tablename__ = 'paypoint'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True, unique=True)
    location = db.Column(db.String(255), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    operating_hours = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    sales = db.relationship('Sale', back_populates='paypoint')

    # Ensure uniqueness of paypoints
    __table_args__ = (
        Index('idx_paypoint_name_status', 'name', 'status'),
        Index('idx_paypoint_location', 'location'),
        Index('idx_paypoint_contact', 'contact_phone', 'contact_email')
    )

    @validates('name')
    def validate_name(self, _, name):
        """Validate that the name is provided and within length limits."""
        if not name or len(name) > 100:
            raise ValueError(
                "Paypoint name must be provided and less than 100 characters"
            )
        return name

    @validates('location')
    def validate_location(self, _, location):
        """Validate that the location is within length limits."""
        if location and len(location) > 255:
            raise ValueError("Location must be less than 255 characters")
        return location

    @validates('contact_phone')
    def validate_contact_phone(self, _, phone):
        """Validate that the contact phone number is valid."""
        if phone and (len(phone) < 10 or len(phone) > 20):
            raise ValueError(
                "Contact phone number must be between 10 and 20 characters"
            )
        return phone

    @validates('contact_email')
    def validate_contact_email(self, _, email):
        """Validate that the contact email is valid."""
        if email and '@' not in email:
            raise ValueError("Invalid email format")
        return email

    @validates('status')
    def validate_status(self, _, status):
        """Validate that the status is one of the allowed values."""
        allowed_statuses = ['active', 'inactive', 'suspended']
        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}"
            )
        return status

    def serialize(self):
        """Return a serialized version of the Paypoint."""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'operating_hours': self.operating_hours,
            'status': self.status,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_paypoints(page=1, per_page=10):
        """Retrieve a paginated list of active (non-deleted) paypoints."""
        try:
            paginated_paypoints = Paypoint.query.filter_by(
                is_deleted=False,
                status='active'
            ).paginate(page=page, per_page=per_page, error_out=False)
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
            paginated_paypoints = Paypoint.query.filter_by(
                is_deleted=True
            ).paginate(page=page, per_page=per_page, error_out=False)
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
            self.status = 'inactive'
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error soft-deleting paypoint: {str(e)}")

    def restore(self):
        """Restore a soft-deleted paypoint (set `is_deleted` to False)."""
        try:
            self.is_deleted = False
            self.status = 'active'
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error restoring paypoint: {str(e)}")

    def suspend(self):
        """Suspend the paypoint (set status to 'suspended')."""
        try:
            self.status = 'suspended'
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error suspending paypoint: {str(e)}")

    def activate(self):
        """Activate the paypoint (set status to 'active')."""
        try:
            self.status = 'active'
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error activating paypoint: {str(e)}")

    @staticmethod
    def get_sales_count(paypoint_id):
        """Get the total number of sales associated with a paypoint."""
        try:
            return db.session.query(db.func.count(Sale.id)).filter_by(
                paypoint_id=paypoint_id,
                is_deleted=False
            ).scalar() or 0
        except Exception as e:
            raise ValueError(f"Error getting sales count: {str(e)}")

    @staticmethod
    def get_total_sales_amount(paypoint_id):
        """Get the total amount of sales associated with a paypoint."""
        try:
            return db.session.query(db.func.sum(Sale.amount)).filter_by(
                paypoint_id=paypoint_id,
                is_deleted=False
            ).scalar() or 0
        except Exception as e:
            raise ValueError(f"Error getting total sales amount: {str(e)}")

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
