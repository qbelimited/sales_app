from app import db
from datetime import datetime
from sqlalchemy.orm import validates
from sqlalchemy import Index

class Inception(db.Model):
    __tablename__ = 'inception'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False, index=True)
    amount_received = db.Column(db.Float, nullable=False)  # Amount of money received from the inception
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Date the money was received
    description = db.Column(db.String(255), nullable=True)  # Optional description of the inception
    payment_method = db.Column(db.String(50), nullable=False, default='cash')  # Method of payment
    status = db.Column(db.String(20), nullable=False, default='completed')  # Status of the inception
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    sale = db.relationship('Sale', backref=db.backref('inceptions', lazy=True))

    # Ensure uniqueness of inceptions within a sale
    __table_args__ = (
        Index('idx_inception_sale_status', 'sale_id', 'status'),
        Index('idx_inception_received_at', 'received_at'),
        Index('idx_inception_payment_method', 'payment_method')
    )

    @validates('amount_received')
    def validate_amount_received(self, key, value):
        """Validate that the amount received is a positive number."""
        if value <= 0:
            raise ValueError("Amount received must be greater than zero.")
        return value

    @validates('received_at')
    def validate_received_at(self, key, value):
        """Validate that the received date is not in the future."""
        if value and value > datetime.utcnow():
            raise ValueError("Received date cannot be in the future.")
        return value

    @validates('payment_method')
    def validate_payment_method(self, key, value):
        """Validate that the payment method is one of the allowed values."""
        allowed_methods = ['cash', 'bank', 'mobile_money', 'cheque', 'paypoint', 'other']
        if value not in allowed_methods:
            raise ValueError(
                f"Invalid payment method. Allowed values are: {', '.join(allowed_methods)}"
            )
        return value

    @validates('status')
    def validate_status(self, key, value):
        """Validate that the status is one of the allowed values."""
        allowed_statuses = ['pending', 'completed', 'cancelled']
        if value not in allowed_statuses:
            raise ValueError(
                f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}"
            )
        return value

    def serialize(self):
        """Return serialized data for the inception."""
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'amount_received': self.amount_received,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'description': self.description,
            'payment_method': self.payment_method,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_inceptions_by_sale(sale_id):
        """Get all inceptions associated with a particular sale."""
        return Inception.query.filter_by(sale_id=sale_id).all()

    @staticmethod
    def get_total_inceptions_by_sale(sale_id):
        """Get the total amount of inceptions for a particular sale."""
        total = db.session.query(
            db.func.sum(Inception.amount_received)
        ).filter_by(
            sale_id=sale_id,
            status='completed'
        ).scalar()
        return total or 0  # Return 0 if no inceptions found

    @staticmethod
    def get_inceptions_by_date_range(start_date, end_date):
        """Get all inceptions received within a given date range."""
        return Inception.query.filter(
            Inception.received_at.between(start_date, end_date)
        ).all()

    @staticmethod
    def get_total_inceptions(start_date=None, end_date=None):
        """Get the total amount of all inceptions, optionally filtered by a date range."""
        query = db.session.query(db.func.sum(Inception.amount_received)).filter_by(
            status='completed'
        )
        if start_date and end_date:
            query = query.filter(Inception.received_at.between(start_date, end_date))
        return query.scalar() or 0  # Return 0 if no inceptions found

    @staticmethod
    def create_inception(sale_id, amount_received, description=None, payment_method='cash'):
        """Create and save a new inception record."""
        inception = Inception(
            sale_id=sale_id,
            amount_received=amount_received,
            description=description,
            payment_method=payment_method,
            received_at=datetime.utcnow()  # Set the received_at time to now
        )
        db.session.add(inception)
        try:
            db.session.commit()
            return inception
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error creating inception: {e}")

    def cancel(self):
        """Cancel the inception."""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error cancelling inception: {e}")

    def is_valid_amount(self):
        """Check if the inception amount is valid against the sale amount."""
        if not self.sale:
            return False
        total_inceptions = Inception.get_total_inceptions_by_sale(self.sale_id)
        return (total_inceptions + self.amount_received) <= self.sale.amount
