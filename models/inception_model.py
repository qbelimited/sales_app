from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Inception(db.Model):
    __tablename__ = 'inception'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False, index=True)
    amount_received = db.Column(db.Float, nullable=False)  # Amount of money received from the inception
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Date the money was received
    description = db.Column(db.String(255), nullable=True)  # Optional description of the inception (e.g., payment method)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    sale = db.relationship('Sale', backref=db.backref('inceptions', lazy=True))

    @validates('amount_received')
    def validate_amount_received(self, key, value):
        """Validate that the amount received is a positive number."""
        if value <= 0:
            raise ValueError("Amount received must be greater than zero.")
        return value

    def serialize(self):
        """Return serialized data for the inception."""
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'amount_received': self.amount_received,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'description': self.description,
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
        total = db.session.query(db.func.sum(Inception.amount_received)).filter_by(sale_id=sale_id).scalar()
        return total or 0  # Return 0 if no inceptions found

    @staticmethod
    def get_inceptions_by_date_range(start_date, end_date):
        """Get all inceptions received within a given date range."""
        return Inception.query.filter(Inception.received_at.between(start_date, end_date)).all()

    @staticmethod
    def get_total_inceptions(start_date=None, end_date=None):
        """Get the total amount of all inceptions, optionally filtered by a date range."""
        query = db.session.query(db.func.sum(Inception.amount_received))
        if start_date and end_date:
            query = query.filter(Inception.received_at.between(start_date, end_date))
        return query.scalar() or 0  # Return 0 if no inceptions found

    @staticmethod
    def create_inception(sale_id, amount_received, description=None):
        """Create and save a new inception record."""
        inception = Inception(
            sale_id=sale_id,
            amount_received=amount_received,
            description=description,
            received_at=datetime.utcnow()  # Set the received_at time to now
        )
        db.session.add(inception)
        try:
            db.session.commit()
            return inception
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error creating inception: {e}")
