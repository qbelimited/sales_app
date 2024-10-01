from app import db, logger
from sqlalchemy import and_, or_
from flask import jsonify, request
from models.bank_model import Bank
from sqlalchemy.orm import validates
from datetime import datetime, timedelta
from models.under_investigation_model import UnderInvestigation

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sale_manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sales_executive_id = db.Column(db.Integer, db.ForeignKey('sales_executive.id'), nullable=False, index=True)
    client_name = db.Column(db.String(150), nullable=False, index=True)
    client_id_no = db.Column(db.String(150), nullable=True)
    client_phone = db.Column(db.String(10), nullable=False, index=True)
    serial_number = db.Column(db.String(100), nullable=False, index=True, unique=True)
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
    user = db.relationship('User', foreign_keys=[user_id], lazy='joined')

    ALLOWED_PLATFORMS = ['', 'Transflow', 'Hubtel', 'company Momo number']
    MAX_RECENT_TRANSACTIONS = 10
    TRANSACTION_PERIOD_DAYS = 30

    @validates('client_phone')
    def validate_client_phone(self, _, number):
        sanitized_number = number.strip()  # Input sanitization
        if len(sanitized_number) != 10 or not sanitized_number.isdigit():
            raise ValueError("Client phone number must be exactly 10 digits")
        return sanitized_number

    @validates('bank_acc_number', 'bank_id')
    def validate_bank_acc_number(self, key, value):
        """Ensure account numbers are valid for selected banks."""
        if key == 'bank_acc_number' and self.bank_id:  # Only validate if bank_id is provided
            bank = Bank.query.get(self.bank_id)
            length = len(value)

            # Define account number length requirements based on bank names
            account_length_requirements = {
                'UBA': 14,
                'Zenith': 10,
                'Absa': 10,
                'SG': [12, 13]
            }

            # Check account number requirements based on the bank name
            for keyword, required_length in account_length_requirements.items():
                if keyword in bank.name:
                    if isinstance(required_length, list):  # Handle cases with multiple valid lengths
                        if length not in required_length:
                            raise ValueError(f"{keyword} account number must be {required_length} digits")
                    else:
                        if length != required_length:
                            raise ValueError(f"{keyword} account number must be {required_length} digits")
                    break  # Exit loop once the matching bank is found

            # Handle generic case if no specific bank requirements were met
            if length not in [13, 16]:
                raise ValueError("Account number must be 13 or 16 digits")
        return value

    @validates('collection_platform')
    def validate_collection_platform(self, _, value):
        if value not in self.ALLOWED_PLATFORMS:
            raise ValueError(f"Invalid collection platform. Must be one of {self.ALLOWED_PLATFORMS}.")
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
            # Add the sale to the session to get its ID
            db.session.add(self)
            db.session.flush()  # This will generate the ID for the sale

            # Normalize and sanitize user inputs
            client_name_normalized = self.sanitize_input(self.client_name.strip().lower())
            client_phone_normalized = self.sanitize_input(self.client_phone.strip())
            client_id_no_normalized = self.sanitize_input(self.client_id_no.strip().lower() or "")
            serial_number_normalized = self.sanitize_input(self.serial_number.strip().lower() or "")
            momo_reference_number_normalized = self.sanitize_input(self.momo_reference_number.strip().lower() or "")
            bank_acc_number_normalized = self.sanitize_input(self.bank_acc_number.strip() or "")

            # Check transaction frequency
            recent_transactions_count = self.get_recent_transaction_count(client_phone_normalized)

            if recent_transactions_count > self.MAX_RECENT_TRANSACTIONS:
                logger.warning(f"High transaction frequency detected for {client_phone_normalized}. Consider flagging for review.")
                self.flag_under_investigation("High transaction frequency detected.")
                return self

            # Check for duplicates
            critical_duplicate = self.find_duplicate(critical=True,
                                                    client_name=client_name_normalized,
                                                    client_phone=client_phone_normalized,
                                                    client_id_no=client_id_no_normalized,
                                                    serial_number=serial_number_normalized,
                                                    momo_reference_number=momo_reference_number_normalized,
                                                    bank_acc_number=bank_acc_number_normalized)

            if critical_duplicate:
                self.status = 'under investigation'
                self.flag_under_investigation("Critical duplicate detected.")
                return self

            less_critical_duplicate = self.find_duplicate(critical=False,
                                                        client_name=client_name_normalized,
                                                        client_phone=client_phone_normalized,
                                                        serial_number=serial_number_normalized)

            if less_critical_duplicate:
                self.status = 'potential duplicate'
                self.flag_under_investigation("Potential duplicate detected.")
                return self

            # No duplicates found, proceed with normal submission
            self.status = 'submitted'
            db.session.commit()
            return self

        except ValueError as ve:
            logger.error(f"Validation error in duplicate check: {ve}")
            db.session.rollback()  # Rollback session on validation errors
            raise ValueError("Validation error: " + str(ve))
        except Exception as e:
            db.session.rollback()  # Ensure rollback on any exception
            logger.error(f"Database error checking for duplicates: {e}")
            raise ValueError("An error occurred while checking for duplicates. Please try again.")

    def get_recent_transaction_count(self, client_phone):
        """Retrieve the count of recent transactions for a client phone number."""
        try:
            return Sale.query.filter(
                Sale.client_phone == client_phone,
                Sale.created_at >= datetime.utcnow() - timedelta(days=self.TRANSACTION_PERIOD_DAYS)
            ).count()
        except Exception as e:
            logger.error(f"Error fetching recent transaction count: {e}")
            raise

    def find_duplicate(self, critical, client_name, client_phone, client_id_no, serial_number, momo_reference_number, bank_acc_number):
        """Check for duplicates based on specified criteria."""
        query = Sale.query.filter(Sale.is_deleted == False, Sale.status.notin_(['under investigation', 'potential duplicate']))

        if critical:
            conditions = or_(
                and_(
                    Sale.client_name == client_name,
                    Sale.client_phone == client_phone,
                    Sale.client_id_no == client_id_no,
                    Sale.policy_type_id == self.policy_type_id
                ),
                and_(
                    Sale.client_phone == client_phone,
                    Sale.serial_number == serial_number,
                    Sale.momo_reference_number == momo_reference_number
                ),
                and_(
                    Sale.client_id_no == client_id_no,
                    Sale.bank_acc_number == bank_acc_number,
                    Sale.serial_number == serial_number
                )
            )
        else:
            conditions = or_(
                and_(
                    Sale.client_name == client_name,
                    Sale.client_phone == client_phone,
                    Sale.policy_type_id == self.policy_type_id
                ),
                and_(
                    Sale.client_phone == client_phone,
                    Sale.serial_number == serial_number
                )
            )

        return query.filter(conditions).first()

    def flag_under_investigation(self, reason):
        """Flag the current sale under investigation and log the reason."""
        self.status = 'under investigation'
        db.session.add(self)
        investigation = UnderInvestigation(
            sale_id=self.id,  # Now self.id is available
            reason=reason,
            notes='Auto-flagged by system based on fraud detection rules'
        )
        db.session.add(investigation)
        db.session.commit()

    def sanitize_input(self, value):
        """Sanitize input to avoid injection attacks."""
        if isinstance(value, str):
            # Strip whitespace and escape special characters
            sanitized_value = value.strip().replace("'", "''")  # Simple SQL escaping
            return sanitized_value
        return value

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
            'bank_acc_number': self.bank_acc_number,
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
            logger.error(f"Error fetching active sales: {e}")
            raise ValueError(f"Error fetching active sales: {e}")

    @staticmethod
    def check_serial_number():
        """Check if a serial number exists."""
        serial_number = request.args.get('serial_number')
        if not serial_number:
            return jsonify({"exists": False, "message": "Serial number not provided"}), 400

        exists = Sale.query.filter_by(serial_number=serial_number).first() is not None
        return jsonify({"exists": exists})
