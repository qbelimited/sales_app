from app import db
from datetime import datetime
from sqlalchemy.orm import validates

# Association table for many-to-many relationship between sales executives and branches
sales_executive_branches = db.Table('sales_executive_branches',
    db.Column('sales_executive_id', db.Integer, db.ForeignKey('sales_executive.id'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id'), primary_key=True)
)

class SalesExecutive(db.Model):
    __tablename__ = 'sales_executive'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    code = db.Column(db.String(100), unique=True, nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    phone_number = db.Column(db.String(10), nullable=True, unique=True, index=True)  # Ensure uniqueness if necessary
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    manager = db.relationship('User', backref='sales_executives')
    branches = db.relationship('Branch', secondary=sales_executive_branches, backref=db.backref('sales_executives', lazy='dynamic'))

    @validates('phone_number')
    def validate_phone_number(self, _, phone_number):
        """Ensure phone number is exactly 10 digits and numeric."""
        if phone_number and (len(phone_number) != 10 or not phone_number.isdigit()):
            raise ValueError("Phone number must be 10 digits and numeric")
        return phone_number

    def serialize(self):
        """Return serialized data for a sales executive."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'manager_id': self.manager_id,
            'phone_number': self.phone_number,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'branches': [branch.serialize() for branch in self.branches]  # Serialize detailed branch info
        }

    @staticmethod
    def get_active_sales_executives(page=1, per_page=10):
        """Retrieve paginated list of active sales executives."""
        try:
            return SalesExecutive.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active sales executives: {e}")

    @staticmethod
    def get_sales_executives_by_manager(manager_id, page=1, per_page=10):
        """Retrieve active sales executives under a specific manager."""
        try:
            return SalesExecutive.query.filter_by(manager_id=manager_id, is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching sales executives by manager: {e}")

    @staticmethod
    def get_sales_executives_by_branch(branch_id, page=1, per_page=10):
        """Retrieve active sales executives for a specific branch."""
        try:
            return SalesExecutive.query.join(SalesExecutive.branches).filter_by(id=branch_id).filter(SalesExecutive.is_deleted == False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching sales executives by branch: {e}")

    @staticmethod
    def soft_delete_sales_executive(executive_id):
        """Soft delete a sales executive by setting the is_deleted flag."""
        try:
            executive = SalesExecutive.query.filter_by(id=executive_id, is_deleted=False).first()
            if executive:
                executive.is_deleted = True
                db.session.commit()
                return True
            else:
                return False
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error soft deleting sales executive: {e}")
