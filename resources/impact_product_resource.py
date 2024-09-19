from flask_restx import Namespace, Resource, fields
from flask import request
from models.impact_product_model import ImpactProduct, ProductCategory
from models.audit_model import AuditTrail
from app import db, logger  # Import logger from app.py
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for Impact Product operations
impact_product_ns = Namespace('impact_product', description='Impact Product operations')

# Define a model for Swagger documentation
impact_product_model = impact_product_ns.model('ImpactProduct', {
    'id': fields.Integer(description='Product ID'),
    'name': fields.String(required=True, description='Product Name'),
    'category': fields.String(required=True, description='Product Category'),
    'group': fields.String(required=True, description='Product Group (risk, investment, hybrid)'),
})

# Helper function to check role permissions
def check_role_permission(current_user, required_role):
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'viewer': ['admin', 'manager', 'viewer']
    }
    return current_user['role'].lower() in roles.get(required_role, [])

@impact_product_ns.route('/')
class ImpactProductListResource(Resource):
    @impact_product_ns.doc(security='Bearer Auth')
    @jwt_required()
    @impact_product_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @impact_product_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @impact_product_ns.param('filter_by', 'Filter by product name or category', type='string')
    @impact_product_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
    def get(self):
        """Retrieve a paginated list of Impact Products."""
        current_user = get_jwt_identity()

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')

        # Ensure sorting by valid fields
        if sort_by not in ['created_at', 'name']:
            logger.error(f"Invalid sort_by field: {sort_by}")
            return {"message": "Invalid sorting field"}, 400

        product_query = ImpactProduct.query.filter_by(is_deleted=False)

        # Filter by product name or category
        if filter_by:
            product_query = product_query.join(ProductCategory).filter(
                (ImpactProduct.name.ilike(f'%{filter_by}%')) |
                (ProductCategory.name.ilike(f'%{filter_by}%'))
            )

        products = product_query.order_by(sort_by).paginate(page=page, per_page=per_page, error_out=False)

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='impact_product_list',
            details="User accessed list of Impact Products"
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'products': [product.serialize() for product in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': products.page
        }, 200

    @impact_product_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Missing required fields', 403: 'Unauthorized'})
    @jwt_required()
    @impact_product_ns.expect(impact_product_model, validate=True)
    def post(self):
        """Create a new Impact Product (admin and manager only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'admin'):
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate category
        category = ProductCategory.query.filter_by(name=data.get('category')).first()
        if not category:
            return {'message': f"Category '{data.get('category')}' not found"}, 400

        new_product = ImpactProduct(
            name=data['name'],
            category=category,
            group=data['group']
        )

        try:
            db.session.add(new_product)
            db.session.commit()

            # Log the creation to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='impact_product',
                resource_id=new_product.id,
                details=f"User created a new Impact Product with ID {new_product.id}"
            )
            db.session.add(audit)
            db.session.commit()

            return new_product.serialize(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating product: {e}")
            return {"message": "Error creating product"}, 500


@impact_product_ns.route('/<int:product_id>')
class ImpactProductResource(Resource):
    @impact_product_ns.doc(security='Bearer Auth', responses={200: 'Success', 404: 'Impact Product not found', 403: 'Unauthorized'})
    @jwt_required()
    def get(self, product_id):
        """Retrieve a specific Impact Product by ID."""
        current_user = get_jwt_identity()
        product = ImpactProduct.query.filter_by(id=product_id, is_deleted=False).first()
        if not product:
            return {'message': 'Impact Product not found'}, 404

        # Log the access to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='ACCESS',
            resource_type='impact_product',
            resource_id=product_id,
            details=f"User accessed Impact Product with ID {product_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return product.serialize(), 200

    @impact_product_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Impact Product not found', 403: 'Unauthorized'})
    @jwt_required()
    @impact_product_ns.expect(impact_product_model, validate=True)
    def put(self, product_id):
        """Update an existing Impact Product (admin and manager only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'manager'):
            return {'message': 'Unauthorized'}, 403

        product = ImpactProduct.query.filter_by(id=product_id, is_deleted=False).first()
        if not product:
            return {'message': 'Impact Product not found'}, 404

        data = request.json
        product.name = data.get('name', product.name)
        product.category = ProductCategory.query.filter_by(name=data.get('category')).first() or product.category
        product.group = data.get('group', product.group)
        product.updated_at = datetime.utcnow()

        db.session.commit()

        # Log the update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='impact_product',
            resource_id=product.id,
            details=f"User updated Impact Product with ID {product.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return product.serialize(), 200

    @impact_product_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Impact Product not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, product_id):
        """Soft-delete an Impact Product (admin only)."""
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'admin'):
            return {'message': 'Unauthorized'}, 403

        product = ImpactProduct.query.filter_by(id=product_id, is_deleted=False).first()
        if not product:
            return {'message': 'Impact Product not found'}, 404

        product.is_deleted = True
        db.session.commit()

        # Log the deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='impact_product',
            resource_id=product.id,
            details=f"User deleted Impact Product with ID {product.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Impact Product deleted successfully'}, 200
