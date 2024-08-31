from app import db
from datetime import datetime

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sale_manager = db.Column(db.String(100), nullable=False)
    sales_executive = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    bank_branch = db.Column(db.String(100), nullable=False)
    bank_acc_number = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=True)
    geolocation = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='submitted')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sale_manager': self.sale_manager,
            'sales_executive': self.sales_executive,
            'branch': self.branch,
            'telephone': self.telephone,
            'bank_name': self.bank_name,
            'bank_branch': self.bank_branch,
            'bank_acc_number': self.bank_acc_number,
            'amount': self.amount,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'geolocation': self.geolocation,
            'status': self.status
        }
