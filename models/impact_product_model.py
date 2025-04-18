from extensions import db
from datetime import datetime
from sqlalchemy.orm import validates
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Index

# Define a new table for product categories
class ProductCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('name')
    def validate_name(self, _, name):
        """Ensure that category name is not empty and trim any spaces."""
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty or whitespace")
        return name.strip()

    def serialize(self):
        """Serialize category data for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
            if self.updated_at else None
        }

    @staticmethod
    def get_all_categories():
        """Retrieve all categories."""
        return ProductCategory.query.order_by(ProductCategory.name.asc()).all()


# Define the ImpactProduct model with category and group columns
class ImpactProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active', index=True)

    # Foreign key relationship to ProductCategory
    category_id = db.Column(
        db.Integer,
        db.ForeignKey('product_category.id'),
        nullable=False
    )
    category = db.relationship('ProductCategory', backref='products', lazy='joined')

    # Group column restricted to three possible values
    group = db.Column(
        db.Enum('risk', 'investment', 'hybrid', name='impact_product_group'),
        nullable=False,
        index=True
    )

    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Ensure uniqueness of product names within categories
    __table_args__ = (
        db.UniqueConstraint('name', 'category_id', name='_product_category_uc'),
        Index('idx_product_category_group', 'category_id', 'group'),
        Index('idx_product_status_group', 'status', 'group')
    )

    @validates('name')
    def validate_name(self, _, name):
        """Ensure the product name is valid."""
        if not name or not name.strip():
            raise ValueError("Product name cannot be empty or whitespace")
        return name.strip()

    @validates('group')
    def validate_group(self, _, group):
        """Ensure that the group is one of the allowed values."""
        allowed_groups = ['risk', 'investment', 'hybrid']
        if group not in allowed_groups:
            raise ValueError(
                f"Invalid group. Allowed values are: {', '.join(allowed_groups)}"
            )
        return group

    @validates('status')
    def validate_status(self, _, status):
        """Ensure that the status is one of the allowed values."""
        allowed_statuses = ['active', 'inactive', 'deprecated']
        if status not in allowed_statuses:
            raise ValueError(
                f"Invalid status. Allowed values are: {', '.join(allowed_statuses)}"
            )
        return status

    def serialize(self):
        """Serialize product data for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'category': self.category.serialize() if self.category else None,
            'group': self.group,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
            if self.updated_at else None
        }

    @staticmethod
    def get_active_products(page=1, per_page=10):
        """Retrieve paginated list of active products."""
        try:
            return ImpactProduct.query.filter_by(
                is_deleted=False,
                status='active'
            ).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active products: {str(e)}")

    @staticmethod
    def get_products_by_group(group, page=1, per_page=10):
        """Retrieve paginated list of products by group."""
        try:
            return ImpactProduct.query.filter_by(
                is_deleted=False,
                status='active',
                group=group
            ).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching products by group: {str(e)}")

    def save(self):
        """Save the product to the database with error handling."""
        try:
            db.session.add(self)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(
                f"Error saving product (duplicate or constraint violation): {str(e)}"
            )
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error saving product: {str(e)}")

    def delete(self, soft_delete=True):
        """Delete or soft-delete the product."""
        try:
            if soft_delete:
                self.is_deleted = True
                self.status = 'inactive'
            else:
                db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error deleting product: {str(e)}")

    @staticmethod
    def get_product_by_id(product_id):
        """Retrieve a single product by its ID."""
        product = ImpactProduct.query.filter_by(
            id=product_id,
            is_deleted=False
        ).first()
        if not product:
            raise ValueError(
                f"Product with ID {product_id} not found or has been deleted."
            )
        return product
