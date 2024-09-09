from app import db
from datetime import datetime

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

    def serialize(self):
        """Return serialized data for the inception."""
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'amount_received': self.amount_received,
            'received_at': self.received_at.isoformat(),
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_inceptions_by_sale(sale_id):
        """Get all inceptions associated with a particular sale."""
        return Inception.query.filter_by(sale_id=sale_id).all()

