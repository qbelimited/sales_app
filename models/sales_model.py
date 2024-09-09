from app import db
from datetime import datetime
from sqlalchemy.orm import validates
from models.under_investigation_model import UnderInvestigation

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sale_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sales_executive_id = db.Column(db.Integer, db.ForeignKey('sales_executive.id'), nullable=False, index=True)
    client_name = db.Column(db.String(150), nullable=False, index=True)
    client_id_no = db.Column(db.String(150), nullable=True, index=True)
    client_phone = db.Column(db.String(10), nullable=False, index=True)
    serial_number = db.Column(db.String(100), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False, index=True)
    momo_reference_number = db.Column(db.String(100), nullable=True, index=True)
    collection_platform = db.Column(db.String(100), nullable=True, index=True)
    momo_transaction_id = db.Column(db.String(100), nullable=True, index=True)
    first_pay_with_momo = db.Column(db.Boolean, nullable=True, index=True)
    subsequent_pay_source_type = db.Column(db.String(50), nullable=True, index=True)
    bank_name = db.Column(db.String(100), nullable=True, index=True)
    bank_branch = db.Column(db.String(100), nullable=True, index=True)
    bank_acc_number = db.Column(db.String(100), nullable=True, index=True)
    paypoint_name = db.Column(db.String(100), nullable=True, index=True)
    paypoint_branch = db.Column(db.String(100), nullable=True, index=True)
    staff_id = db.Column(db.String(100), nullable=True, index=True)
    policy_type_id = db.Column(db.Integer, db.ForeignKey('impact_product.id'), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    geolocation_latitude = db.Column(db.Float, nullable=True)
    geolocation_longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='submitted', index=True)
    customer_called = db.Column(db.Boolean, default=False)
    momo_first_premium = db.Column(db.Boolean, default=False)

    # Relationships
    policy_type = db.relationship('ImpactProduct', backref=db.backref('sales', lazy=True))
    sale_manager = db.relationship('User', foreign_keys=[sale_manager_id])

    # Validators
    @validates('client_phone')
    def validate_client_phone(self, _, number):
        if len(number) != 10 or not number.isdigit():
            raise ValueError("Client phone number must be exactly 10 digits")
        return number

    @validates('bank_acc_number', 'bank_name')
    def validate_bank_acc_number(self, key, value):
        if key == 'bank_acc_number' and self.bank_name:
            length = len(value)
            if 'UBA' in self.bank_name and length != 14:
                raise ValueError("UBA account number must be 14 digits")
            elif ('Zenith' in self.bank_name or 'Absa' in self.bank_name) and length != 10:
                raise ValueError("Zenith or Absa account number must be 10 digits")
            elif 'SG' in self.bank_name and length not in [12, 13]:
                raise ValueError("SG account number must be 12 or 13 digits")
            elif length not in [13, 16]:
                raise ValueError("Account number must be 13 or 16 digits")
        return value

    @validates('collection_platform')
    def validate_collection_platform(self, _, value):
        allowed_platforms = ['Transflow', 'Hubtel', 'company Momo number']
        if value not in allowed_platforms:
            raise ValueError(f"Invalid collection platform. Must be one of {allowed_platforms}.")
        return value

    def check_duplicate(self):
        try:
            duplicate_conditions = (
                # Same duplicate check logic as before
            )
            duplicate_sale = Sale.query.filter(*duplicate_conditions).first()
            phone_duplicate = Sale.query.filter(Sale.client_phone == self.client_phone, Sale.is_deleted == False).first()
            name_duplicate = Sale.query.filter(Sale.client_name == self.client_name, Sale.is_deleted == False).first()

            if duplicate_sale or phone_duplicate or name_duplicate:
                self.status = 'under investigation'
                reason = 'Duplicate detected'
                if phone_duplicate:
                    reason += ' (Duplicate phone number)'
                if name_duplicate:
                    reason += ' (Duplicate client name)'

                investigation = UnderInvestigation(
                    sale_id=self.id,
                    reason=reason,
                    notes='Auto-flagged by system'
                )
                db.session.add(investigation)
            return self
        except Exception as e:
            raise ValueError(f"Error checking for duplicates: {e}")

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sale_manager': self.sale_manager.serialize(),  # Serialize the sales manager from User
            'sales_executive_id': self.sales_executive_id,
            'client_name': self.client_name,
            'client_id_no': self.client_id_no,
            'client_phone': self.client_phone,
            'serial_number': self.serial_number,
            'source_type': self.source_type,
            'momo_reference_number': self.momo_reference_number,
            'collection_platform': self.collection_platform,  # Ensure collection platform is serialized
            'momo_transaction_id': self.momo_transaction_id,
            'first_pay_with_momo': self.first_pay_with_momo,
            'subsequent_pay_source_type': self.subsequent_pay_source_type,
            'bank_name': self.bank_name,
            'bank_branch': self.bank_branch,
            'bank_acc_number': self.bank_acc_number,
            'paypoint_name': self.paypoint_name,
            'paypoint_branch': self.paypoint_branch,
            'staff_id': self.staff_id,
            'policy_type': self.policy_type.serialize(),  # Serialize the policy type
            'amount': self.amount,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
            'geolocation_latitude': self.geolocation_latitude,
            'geolocation_longitude': self.geolocation_longitude,
            'status': self.status,
            'customer_called': self.customer_called,
            'momo_first_premium': self.momo_first_premium
        }
