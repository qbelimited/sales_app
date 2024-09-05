from app import db
from datetime import datetime
from sqlalchemy.orm import validates
from models.under_investigation_model import UnderInvestigation
from models.impact_product_model import ImpactProduct

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sale_manager = db.Column(db.String(100), nullable=False, index=True)
    sales_executive_id = db.Column(db.Integer, db.ForeignKey('sales_executive.id'), nullable=False, index=True)
    client_name = db.Column(db.String(150), nullable=False, index=True)  # Client name
    client_phone = db.Column(db.String(10), nullable=False, index=True)  # Client phone number, must be 10 digits
    serial_number = db.Column(db.String(100), nullable=False, index=True)  # Serial number field
    source_type = db.Column(db.String(50), nullable=False, index=True)  # 'momo', 'bank', or 'paypoint'
    momo_reference_number = db.Column(db.String(100), nullable=True, index=True)  # Momo reference number, required if source_type is 'momo'
    momo_transaction_id = db.Column(db.String(100), nullable=True, index=True)  # Momo transaction ID, required if source_type is 'momo'
    first_pay_with_momo = db.Column(db.Boolean, nullable=True, index=True)  # Yes or No, required if first payment with Momo
    subsequent_pay_source_type = db.Column(db.String(50), nullable=True, index=True)  # 'bank' or 'paypoint', required if first_pay_with_momo is Yes
    bank_name = db.Column(db.String(100), nullable=True, index=True)  # Bank name, required if source_type or subsequent_pay_source_type is 'bank'
    bank_branch = db.Column(db.String(100), nullable=True, index=True)  # Bank branch, required if source_type or subsequent_pay_source_type is 'bank'
    bank_acc_number = db.Column(db.String(100), nullable=True, index=True)  # Bank account number, required if source_type or subsequent_pay_source_type is 'bank'
    paypoint_name = db.Column(db.String(100), nullable=True, index=True)  # Paypoint name, required if source_type or subsequent_pay_source_type is 'paypoint'
    paypoint_branch = db.Column(db.String(100), nullable=True, index=True)  # Paypoint branch, if applicable
    staff_id = db.Column(db.String(100), nullable=True, index=True)  # Staff ID, required if source_type or subsequent_pay_source_type is 'bank' or 'paypoint'
    policy_type_id = db.Column(db.Integer, db.ForeignKey('impact_product.id'), nullable=False, index=True)  # Foreign key to ImpactProduct
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    geolocation_latitude = db.Column(db.Float, nullable=True)
    geolocation_longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='submitted', index=True)  # Status, e.g., 'submitted', 'under investigation'
    customer_called = db.Column(db.Boolean, default=False)  # Checkbox to indicate if the customer was called

    # Relationships
    policy_type = db.relationship('ImpactProduct', backref=db.backref('sales', lazy=True))

    @validates('client_phone')
    def validate_client_phone(self, key, number):
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

    def check_duplicate(self):
        # Flagging duplicates
        duplicate_conditions = (
            (Sale.client_phone == self.client_phone),
            (Sale.serial_number == self.serial_number),
            (Sale.source_type == self.source_type),
            (Sale.momo_reference_number == self.momo_reference_number),
            (Sale.momo_transaction_id == self.momo_transaction_id),
            (Sale.bank_name == self.bank_name),
            (Sale.bank_branch == self.bank_branch),
            (Sale.bank_acc_number == self.bank_acc_number),
            (Sale.paypoint_name == self.paypoint_name),
            (Sale.paypoint_branch == self.paypoint_branch),
            (Sale.staff_id == self.staff_id),
            (Sale.amount == self.amount),
            (Sale.is_deleted == False)
        )

        duplicate_sale = Sale.query.filter(*duplicate_conditions).first()

        # Flag duplicates
        if duplicate_sale or Sale.query.filter_by(staff_id=self.staff_id).count() > 1:
            self.status = 'under investigation'

        if self.status == 'under investigation':
            investigation = UnderInvestigation(
                sale_id=self.id,
                reason='Duplicate detected',  # Customize based on specific reason
                notes='Auto-flagged by system'
            )
            db.session.add(investigation)
        return self

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sale_manager': self.sale_manager,
            'sales_executive_id': self.sales_executive_id,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'serial_number': self.serial_number,
            'source_type': self.source_type,
            'momo_reference_number': self.momo_reference_number,
            'momo_transaction_id': self.momo_transaction_id,
            'first_pay_with_momo': self.first_pay_with_momo,
            'subsequent_pay_source_type': self.subsequent_pay_source_type,
            'bank_name': self.bank_name,
            'bank_branch': self.bank_branch,
            'bank_acc_number': self.bank_acc_number,
            'paypoint_name': self.paypoint_name,
            'paypoint_branch': self.paypoint_branch,
            'staff_id': self.staff_id,
            'policy_type': self.policy_type.serialize(),  # Serialize the policy type (ImpactProduct)
            'amount': self.amount,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
            'geolocation_latitude': self.geolocation_latitude,
            'geolocation_longitude': self.geolocation_longitude,
            'status': self.status,
            'customer_called': self.customer_called
        }
