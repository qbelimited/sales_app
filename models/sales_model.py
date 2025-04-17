from app import db, logger
from sqlalchemy import and_, or_, not_
from flask import jsonify, request
from models.bank_model import Bank
from sqlalchemy.orm import validates, selectinload
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

    # Modify fraud detection fields and constants
    transaction_velocity = db.Column(db.Integer, default=0)  # Transactions per hour
    amount_deviation = db.Column(db.Float, nullable=True)  # Deviation from average
    information_risk_score = db.Column(db.Float, nullable=True)  # Risk based on info quality
    device_fingerprint = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    session_duration = db.Column(db.Integer, nullable=True)

    # Update constants for fraud detection
    MAX_HOURLY_TRANSACTIONS = 20  # Increased for high-volume locations
    AMOUNT_DEVIATION_THRESHOLD = 3.0  # Increased threshold
    MIN_SESSION_DURATION = 15  # Reduced minimum time
    INFO_RISK_THRESHOLD = 0.8  # New threshold for information quality

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
                'UNITED BANK FOR AFRICA': 14,
                'ZENITH': 10,
                'ABSA': 10,
                'SOCIETE GENERAL': [12, 13]
            }

            # Convert the bank name to lowercase for case-insensitive comparison
            bank_name_lower = bank.name.lower()

            # Check account number requirements based on the bank name
            for keyword, required_length in account_length_requirements.items():
                if keyword.lower() in bank_name_lower:  # Compare in lowercase
                    if isinstance(required_length, list):  # Handle cases with multiple valid lengths
                        if length not in required_length:
                            raise ValueError(f"{keyword} account number must be {required_length} digits")
                    else:
                        if length != required_length:
                            raise ValueError(f"{keyword} account number must be {required_length} digits")
                    break  # Exit loop once the matching bank is found

            # Check for other banks and generic length requirements
            if length not in [10, 12, 13, 14, 16]:
                raise ValueError("Account number must be 10, 12, 13, 14, or 16 digits")
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

    def calculate_fraud_indicators(self):
        """Calculate fraud indicators focusing on information quality"""
        try:
            # Calculate transaction velocity
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            self.transaction_velocity = db.session.query(
                db.func.count(Sale.id)
            ).filter(
                Sale.client_phone == self.client_phone,
                Sale.created_at >= hour_ago,
                not_(Sale.is_deleted)
            ).scalar()

            # Calculate amount deviation
            avg_amount = db.session.query(
                db.func.avg(Sale.amount)
            ).filter(
                Sale.policy_type_id == self.policy_type_id,
                not_(Sale.is_deleted)
            ).scalar() or 0

            if avg_amount > 0:
                self.amount_deviation = self.amount / avg_amount

            # Calculate information risk score
            self.information_risk_score = self._calculate_info_risk()

            return True
        except Exception as e:
            logger.error(f"Error calculating fraud indicators: {str(e)}")
            return False

    def _calculate_info_risk(self):
        """Calculate risk based on information quality and consistency"""
        try:
            risk_score = 0.0
            total_checks = 0

            # Check client information completeness
            if self.client_name and len(self.client_name.strip()) > 2:
                total_checks += 1
            if self.client_phone and len(self.client_phone.strip()) == 10:
                total_checks += 1
            if self.client_id_no and len(self.client_id_no.strip()) >= 6:
                total_checks += 1

            # Check payment information consistency
            if self.collection_platform:
                total_checks += 1
                if self.collection_platform == 'Momo' and self.momo_reference_number:
                    total_checks += 1
                elif self.collection_platform == 'Bank' and self.bank_acc_number:
                    total_checks += 1

            # Check policy information
            if self.policy_type_id and self.amount > 0:
                total_checks += 1

            # Calculate final risk score (lower is better)
            if total_checks > 0:
                risk_score = 1.0 - (total_checks / 7.0)  # 7 is max possible checks

            return risk_score
        except Exception as e:
            logger.error(f"Error calculating info risk: {str(e)}")
            return 0.5

    def check_duplicate(self):
        """Enhanced duplicate and fraud checking focusing on information quality"""
        try:
            # Calculate fraud indicators
            if not self.calculate_fraud_indicators():
                raise ValueError("Failed to calculate fraud indicators")

            # Check transaction velocity with higher threshold
            if self.transaction_velocity > self.MAX_HOURLY_TRANSACTIONS:
                logger.warning(
                    f"High transaction velocity detected: {self.transaction_velocity}"
                )
                self.flag_under_investigation("High transaction velocity")
                return self

            # Check amount deviation with higher threshold
            if self.amount_deviation and self.amount_deviation > self.AMOUNT_DEVIATION_THRESHOLD:
                logger.warning(
                    f"Unusual amount deviation detected: {self.amount_deviation}x"
                )
                self.flag_under_investigation("Unusual transaction amount")
                return self

            # Check information quality
            if self.information_risk_score and self.information_risk_score > self.INFO_RISK_THRESHOLD:
                logger.warning(
                    f"Poor information quality detected: {self.information_risk_score}"
                )
                self.flag_under_investigation("Poor information quality")
                return self

            # Check session duration with lower threshold
            if self.session_duration and self.session_duration < self.MIN_SESSION_DURATION:
                logger.warning(
                    f"Suspiciously quick transaction: {self.session_duration}s"
                )
                self.flag_under_investigation("Suspicious transaction speed")
                return self

            # Continue with existing duplicate checks
            return super().check_duplicate()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in enhanced fraud check: {str(e)}")
            raise ValueError("An error occurred during fraud detection")

    def get_recent_transaction_count(self, client_phone):
        """Retrieve the count of recent transactions for a client phone number with optimized query"""
        try:
            # Use a subquery for better performance
            thirty_days_ago = datetime.utcnow() - timedelta(days=self.TRANSACTION_PERIOD_DAYS)

            return db.session.query(
                db.func.count(Sale.id)
            ).filter(
                Sale.client_phone == client_phone,
                Sale.created_at >= thirty_days_ago,
                not_(Sale.is_deleted)
            ).scalar()

        except Exception as e:
            logger.error(f"Error fetching recent transaction count: {e}")
            raise

    def find_duplicate(self, critical, client_phone=None, client_id_no=None, serial_number=None, momo_reference_number=None, bank_acc_number=None):
        """Check for duplicates based on specified criteria with optimized querying"""
        try:
            # Start with a base query using index hints
            query = Sale.query.filter(
                not_(Sale.is_deleted),  # Use not_ instead of == False
                Sale.status.notin_(['under investigation', 'potential duplicate'])
            )

            if critical:
                # Use compound indexes for critical checks with optimized conditions
                conditions = []

                # Check for exact matches first (most critical)
                if client_phone and serial_number:
                    conditions.append(
                        and_(
                            Sale.client_phone == client_phone,
                            Sale.serial_number == serial_number
                        )
                    )

                # Check for ID number matches with policy type
                if client_id_no and self.policy_type_id:
                    conditions.append(
                        and_(
                            Sale.client_id_no == client_id_no,
                            Sale.policy_type_id == self.policy_type_id
                        )
                    )

                # Check for bank account and reference number matches
                if bank_acc_number and momo_reference_number:
                    conditions.append(
                        and_(
                            Sale.bank_acc_number == bank_acc_number,
                            Sale.momo_reference_number == momo_reference_number
                        )
                    )

                if conditions:
                    # Use union to combine results efficiently
                    subqueries = []
                    for condition in conditions:
                        subquery = query.filter(condition)
                        subqueries.append(subquery)

                    if subqueries:
                        final_query = subqueries[0]
                        for subquery in subqueries[1:]:
                            final_query = final_query.union(subquery)
                        return final_query.limit(100).all()
            else:
                # Non-critical checks with simpler conditions
                conditions = []

                # Check for phone number matches with policy type
                if client_phone and self.policy_type_id:
                    conditions.append(
                        and_(
                            Sale.client_phone == client_phone,
                            Sale.policy_type_id == self.policy_type_id
                        )
                    )

                # Check for serial number matches
                if serial_number:
                    conditions.append(
                        Sale.serial_number == serial_number
                    )

                if conditions:
                    query = query.filter(or_(*conditions))
                    return query.limit(100).all()

            return []

        except Exception as e:
            logger.error(f"Error finding duplicates: {str(e)}")
            return []

    def flag_under_investigation(self, reason):
        """Flag the current sale under investigation and log the reason."""
        self.status = 'under investigation'

        # Retrieve all duplicates meeting the conditions for the current sale
        duplicate_sales = self.find_duplicate(
            critical=True,
            client_phone=self.sanitize_input(self.client_phone.strip()),
            client_id_no=self.sanitize_input(self.client_id_no.strip().lower() or ""),
            serial_number=self.sanitize_input(self.serial_number.strip().lower() or ""),
            momo_reference_number=self.sanitize_input(self.momo_reference_number.strip().lower() or ""),
            bank_acc_number=self.sanitize_input(self.bank_acc_number.strip() or "")
        )

        # Collect IDs of duplicate sales
        duplicate_ids = [sale.id for sale in duplicate_sales] if duplicate_sales else []

        # Format notes with duplicate IDs
        notes = f"Auto-flagged by system based on fraud detection rules [with sales_id {', '.join(map(str, duplicate_ids))}]"

        db.session.add(self)
        investigation = UnderInvestigation(
            sale_id=self.id,
            reason=reason,
            notes=notes  # Include duplicate IDs in the notes
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
        """Get active sales with optimized querying for large datasets"""
        try:
            # Use selectinload for efficient relationship loading
            # Add index hints for better query performance
            query = Sale.query.options(
                selectinload(Sale.policy_type),
                selectinload(Sale.sales_executive),
                selectinload(Sale.paypoint),
                selectinload(Sale.sale_manager),
                selectinload(Sale.bank),
                selectinload(Sale.bank_branch),
                selectinload(Sale.user)
            ).filter(
                Sale.is_deleted == False
            ).order_by(
                Sale.created_at.desc()
            )

            # Optimize pagination for large datasets
            # Use keyset pagination for better performance
            if page > 1:
                last_sale = query.limit((page-1) * per_page).all()[-1]
                query = query.filter(Sale.created_at < last_sale.created_at)

            # Get only the current page
            current_page_sales = query.limit(per_page).all()

            # Get total count efficiently
            total_count = db.session.query(db.func.count(Sale.id)).filter(
                Sale.is_deleted == False
            ).scalar()

            total_pages = (total_count + per_page - 1) // per_page

            return {
                'sales': [sale.serialize() for sale in current_page_sales],
                'total': total_count,
                'pages': total_pages,
                'current_page': page
            }
        except Exception as e:
            logger.error(f"Error getting active sales: {str(e)}")
            return {'error': 'Failed to fetch sales'}, 500

    @staticmethod
    def check_serial_number():
        """Check if a serial number exists."""
        serial_number = request.args.get('serial_number')
        if not serial_number:
            return jsonify({"exists": False, "message": "Serial number not provided"}), 400

        exists = Sale.query.filter_by(serial_number=serial_number).first() is not None
        return jsonify({"exists": exists})

    def get_performance_metrics(self):
        """Calculate performance metrics for the sale."""
        try:
            metrics = {
                'fraud_risk_score': self.information_risk_score or 0.0,
                'transaction_velocity': self.transaction_velocity,
                'amount_deviation': self.amount_deviation or 0.0
            }
            return metrics
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}

    def get_customer_retention_metrics(self):
        """Calculate customer retention metrics."""
        try:
            # Get all sales for this customer
            customer_sales = Sale.query.filter(
                Sale.client_phone == self.client_phone,
                not_(Sale.is_deleted)
            ).order_by(Sale.created_at.desc()).all()

            if not customer_sales:
                return {}

            # Calculate metrics
            total_sales = len(customer_sales)
            total_amount = sum(sale.amount for sale in customer_sales)
            avg_time_between_sales = 0
            if total_sales > 1:
                time_diffs = [(customer_sales[i].created_at - customer_sales[i+1].created_at).days
                            for i in range(total_sales-1)]
                avg_time_between_sales = sum(time_diffs) / len(time_diffs)

            return {
                'total_sales': total_sales,
                'total_amount': total_amount,
                'avg_time_between_sales': avg_time_between_sales,
                'first_sale_date': customer_sales[-1].created_at,
                'last_sale_date': customer_sales[0].created_at
            }
        except Exception as e:
            logger.error(f"Error calculating retention metrics: {str(e)}")
            return {}
