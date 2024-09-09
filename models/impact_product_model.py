from app import db
from datetime import datetime
from sqlalchemy.orm import validates

# Define a new table for product categories
class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }


# Define the ImpactProduct model with category and group columns
class ImpactProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)

    # Foreign key relationship to ProductCategory
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.id'), nullable=False)
    category = db.relationship('ProductCategory', backref='products', lazy='joined')

    # Group column restricted to three possible values
    group = db.Column(db.Enum('risk', 'investment', 'hybrid', name='impact_product_group'), nullable=False, index=True)

    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Ensure uniqueness of product names within categories
    __table_args__ = (db.UniqueConstraint('name', 'category_id', name='_product_category_uc'),)

    @validates('name')
    def validate_name(self, _, name):
        if not name:
            raise ValueError("Product name cannot be empty")
        return name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.serialize() if self.category else None,
            'group': self.group,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_products(page=1, per_page=10):
        """Retrieve paginated list of active products."""
        try:
            return ImpactProduct.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active products: {e}")
