from app import db, logger
from datetime import datetime
from sqlalchemy.orm import validates
from models.under_investigation_model import UnderInvestigation
from models.bank_model import Bank
from sqlalchemy import and_, or_

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sale_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sales_executive_id = db.Column(db.Integer, db.ForeignKey('sales_executive.id'), nullable=False, index=True)
    client_name = db.Column(db.String(150), nullable=False, index=True)
    client_id_no = db.Column(db.String(150), nullable=True)
    client_phone = db.Column(db.String(10), nullable=False, index=True)
    serial_number = db.Column(db.String(100), nullable=False, index=True)
    source_type = db.Column(db.String(50), nullable=False)
    momo_reference_number = db.Column(db.String(100), nullable=True)
    collection_platform = db.Column(db.String(100), nullable=True)  # Transflow, Hubtel, Momo
    momo_transaction_id = db.Column(db.String(100), nullable=True)
    first_pay_with_momo = db.Column(db.Boolean, nullable=True)
    subsequent_pay_source_type = db.Column(db.String(50), nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('bank.id'), nullable=True, index=True)
    bank_branch_id = db.Column(db.Integer, db.ForeignKey('bank_branch.id'), nullable=True)
    bank_acc_number = db.Column(db.String(100), nullable=True)
    paypoint_id = db.Column(db.Integer, db.ForeignKey('paypoint.id'), nullable=True, index=True)
    paypoint_branch = db.Column(db.String(100), nullable=True)
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
    policy_type = db.relationship('ImpactProduct', foreign_keys=[policy_type_id], lazy='joined')
    sales_executive = db.relationship('SalesExecutive', foreign_keys=[sales_executive_id], lazy='joined')
    paypoint = db.relationship('Paypoint', foreign_keys=[paypoint_id], lazy='joined')
    sale_manager = db.relationship('User', foreign_keys=[sale_manager_id], lazy='joined')
    bank = db.relationship('Bank', foreign_keys=[bank_id], lazy='joined')
    bank_branch = db.relationship('BankBranch', foreign_keys=[bank_branch_id], lazy='joined')

    @validates('client_phone')
    def validate_client_phone(self, _, number):
        if len(number) != 10 or not number.isdigit():
            raise ValueError("Client phone number must be exactly 10 digits")
        return number

    @validates('bank_acc_number', 'bank_id')
    def validate_bank_acc_number(self, key, value):
        """Ensure account numbers are valid for selected banks."""
        if key == 'bank_acc_number':
            if self.bank_id:  # Only validate if bank_id is provided
                bank = Bank.query.get(self.bank_id)
                length = len(value)
                if bank.name == 'UBA' and length != 14:
                    raise ValueError("UBA account number must be 14 digits")
                elif (bank.name == 'Zenith' or bank.name == 'Absa') and length != 10:
                    raise ValueError("Zenith or Absa account number must be 10 digits")
                elif bank.name == 'SG' and length not in [12, 13]:
                    raise ValueError("SG account number must be 12 or 13 digits")
                elif length not in [13, 16]:
                    raise ValueError("Account number must be 13 or 16 digits")
        return value

    @validates('collection_platform')
    def validate_collection_platform(self, _, value):
        allowed_platforms = ['', 'Transflow', 'Hubtel', 'company Momo number']
        if value not in allowed_platforms:
            raise ValueError(f"Invalid collection platform. Must be one of {allowed_platforms}.")
        return value

    @validates('geolocation_latitude', 'geolocation_longitude')
    def validate_geolocation(self, key, value):
        """Ensure the latitude and longitude are within valid ranges."""
        if key == 'geolocation_latitude':
            if value is not None and (value < -90 or value > 90):
                raise ValueError("Latitude must be between -90 and 90")
        elif key == 'geolocation_longitude':
            if value is not None and (value < -180 or value > 180):
                raise ValueError("Longitude must be between -180 and 180")
        return value

    def check_duplicate(self):
        """Check for duplicate sale based on combinations of key fields, including phone number."""
        try:
            # Ensure the sale ID is not part of the search for duplicates (new sales won't have an ID yet)
            query = Sale.query.filter(Sale.is_deleted == False)

            if self.id:
                query = query.filter(Sale.id != self.id)  # Exclude self from the query for updates

            # Normalize client name and phone for consistent matching (strip spaces, make lowercase)
            client_name_normalized = self.client_name.strip().lower()
            client_phone_normalized = self.client_phone.strip()

            # Define refined potential duplicate conditions (combinations of three key fields including phone number)
            critical_conditions = or_(
                and_(
                    Sale.client_name.ilike(f'%{client_name_normalized}%'),
                    Sale.client_phone == client_phone_normalized,
                    Sale.client_id_no == self.client_id_no
                ),
                and_(
                    Sale.client_phone == client_phone_normalized,
                    Sale.serial_number == self.serial_number,
                    Sale.momo_reference_number == self.momo_reference_number
                ),
                and_(
                    Sale.client_id_no == self.client_id_no,
                    Sale.bank_acc_number == self.bank_acc_number,
                    Sale.serial_number == self.serial_number
                )
            )

            # Define less critical conditions (combinations of two fields including phone number)
            less_critical_conditions = or_(
                and_(
                    Sale.client_name.ilike(f'%{client_name_normalized}%'),
                    Sale.client_phone == client_phone_normalized
                ),
                and_(
                    Sale.client_phone == self.client_phone,
                    Sale.serial_number == self.serial_number
                )
            )

            # Check for critical duplicates
            critical_duplicate = query.filter(critical_conditions).first()
            # Check for less critical duplicates
            potential_duplicate = query.filter(less_critical_conditions).first()

            if critical_duplicate:
                # Mark this sale as 'under investigation'
                self.status = 'under investigation'
                with db.session.begin():
                    investigation = UnderInvestigation(
                        sale_id=self.id,
                        reason='Critical duplicate detected',
                        notes='Auto-flagged by system based on three matching fields'
                    )
                    db.session.add(investigation)
                    db.session.commit()
            elif potential_duplicate:
                # Optionally mark this sale as a "potential duplicate" for manual review
                self.status = 'potential duplicate'
                with db.session.begin():
                    investigation = UnderInvestigation(
                        sale_id=self.id,
                        reason='Potential duplicate detected',
                        notes='Auto-flagged by system based on two matching fields'
                    )
                    db.session.add(investigation)
                    db.session.commit()
            else:
                # Mark this sale as 'new' if no duplicates are found
                self.status = 'submitted'

            return self

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error checking for duplicates: {e}")
            raise ValueError("An error occurred while checking for duplicates. Please try again.")

    def serialize(self):
        """Serialize the sale object for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sale_manager': self.sale_manager.serialize() if self.sale_manager else None,
            'sales_executive_id': self.sales_executive_id,
            'client_name': self.client_name,
            'client_id_no': self.client_id_no,
            'client_phone': self.client_phone,
            'serial_number': self.serial_number,
            'source_type': self.source_type,
            'momo_reference_number': self.momo_reference_number,
            'collection_platform': self.collection_platform,
            'momo_transaction_id': self.momo_transaction_id,
            'first_pay_with_momo': self.first_pay_with_momo,
            'subsequent_pay_source_type': self.subsequent_pay_source_type,
            'bank': self.bank.serialize() if self.bank else None,
            'bank_branch': self.bank_branch.serialize() if self.bank_branch else None,
            'staff_id': self.staff_id,
            'paypoint': self.paypoint.serialize() if self.paypoint else None,
            'paypoint_branch': self.paypoint_branch,
            'policy_type': self.policy_type.serialize() if self.policy_type else None,
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

    @staticmethod
    def get_active_sales(page=1, per_page=10):
        """Retrieve paginated list of active (non-deleted) sales."""
        try:
            sales = Sale.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page)
            return sales.items, sales.total, sales.pages, sales.page
        except Exception as e:
            raise ValueError(f"Error fetching active sales: {e}")
