from flask_restx import Namespace, Resource, fields
from flask import request
from models.impact_product_model import ImpactProduct, ProductCategory
from models.audit_model import AuditTrail
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip
from typing import Dict, Any


# Define a namespace for Impact Product operations
impact_product_ns = Namespace(
    'impact_product',
    description='Impact Product operations'
)

# Define models for Swagger documentation
impact_product_model = impact_product_ns.model(
    'ImpactProduct',
    {
        'id': fields.Integer(
            description='Product ID'
        ),
        'name': fields.String(
            required=True,
            description='Product Name'
        ),
        'description': fields.String(
            description='Product Description'
        ),
        'category': fields.Nested(
            impact_product_ns.model(
                'ProductCategory',
                {
                    'id': fields.Integer(
                        description='Category ID'
                    ),
                    'name': fields.String(
                        description='Category Name'
                    ),
                    'description': fields.String(
                        description='Category Description'
                    )
                }
            )
        ),
        'group': fields.String(
            required=True,
            description='Product Group (risk, investment, hybrid)'
        ),
        'status': fields.String(
            description='Product Status (active, inactive, deprecated)'
        ),
        'is_deleted': fields.Boolean(
            description='Whether the product is deleted'
        ),
        'created_at': fields.DateTime(
            description='Creation timestamp'
        ),
        'updated_at': fields.DateTime(
            description='Last update timestamp'
        )
    }
)


# Helper function to check role permissions
def check_role_permission(
    current_user: Dict[str, Any],
    required_role: str
) -> bool:
    """
    Check if the current user has the required role permission.

    Args:
        current_user: Dictionary containing user information
        required_role: The role to check against

    Returns:
        bool: True if user has permission, False otherwise
    """
    roles = {
        'admin': ['admin'],
        'manager': ['admin', 'manager'],
        'back_office': [
            'admin',
            'manager',
            'back_office'
        ],
        'sales_manager': [
            'admin',
            'manager',
            'back_office',
            'sales_manager'
        ]
    }
    return current_user['role'].lower() in roles.get(
        required_role,
        []
    )


@impact_product_ns.route('/')
class ImpactProductListResource(Resource):
    @impact_product_ns.doc(security='Bearer Auth')
    @jwt_required()
    @impact_product_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @impact_product_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @impact_product_ns.param('filter_by', 'Filter by product name or category', type='string')
    @impact_product_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
    @impact_product_ns.param('group', 'Filter by product group', type='string')
    @impact_product_ns.param('status', 'Filter by product status', type='string')
    def get(self) -> Dict[str, Any]:
        """
        Retrieve a paginated list of Impact Products with optional filtering.

        Returns:
            Dictionary containing paginated products and metadata
        """
        current_user = get_jwt_identity()

        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_by = request.args.get('filter_by', None)
        sort_by = request.args.get('sort_by', 'created_at')
        group = request.args.get('group', None)
        status = request.args.get('status', None)

        # Validate sorting field
        if sort_by not in ['created_at', 'name', 'group', 'status']:
            logger.error(f"Invalid sort_by field: {sort_by}")
            return {"message": "Invalid sorting field"}, 400

        # Build base query
        product_query = ImpactProduct.query.filter_by(is_deleted=False)

        # Apply filters
        if filter_by:
            product_query = product_query.join(ProductCategory).filter(
                (ImpactProduct.name.ilike(f'%{filter_by}%')) |
                (ProductCategory.name.ilike(f'%{filter_by}%'))
            )
        if group:
            product_query = product_query.filter_by(group=group)
        if status:
            product_query = product_query.filter_by(status=status)

        # Apply sorting and pagination
        products = product_query.order_by(sort_by).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # Log the access to audit trail
        try:
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='impact_product_list',
                details="User accessed list of Impact Products",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error logging audit trail: {e}")
            db.session.rollback()

        return {
            'products': [product.serialize() for product in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': products.page,
            'per_page': products.per_page
        }

    @impact_product_ns.doc(security='Bearer Auth', responses={201: 'Created', 400: 'Missing required fields', 403: 'Unauthorized'})
    @jwt_required()
    @impact_product_ns.expect(impact_product_model, validate=True)
    def post(self) -> Dict[str, Any]:
        """
        Create a new Impact Product (admin and manager only).

        Returns:
            Dictionary containing the created product data
        """
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'manager'):
            return {'message': 'Unauthorized'}, 403

        data = request.json

        # Validate required fields
        if not all(key in data for key in ['name', 'category', 'group']):
            return {'message': 'Missing required fields'}, 400

        # Validate category
        category = ProductCategory.query.filter_by(name=data.get('category')).first()
        if not category:
            return {'message': f"Category '{data.get('category')}' not found"}, 400

        # Create new product
        new_product = ImpactProduct(
            name=data['name'],
            description=data.get('description'),
            category=category,
            group=data['group'],
            status=data.get('status', 'active')
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
                details=f"User created a new Impact Product with ID {new_product.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return new_product.serialize(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating product: {e}")
            return {"message": "Error creating product"}, 500


@impact_product_ns.route(
    '/<int:product_id>',
    methods=['GET', 'PUT', 'DELETE']
)
@impact_product_ns.doc(
    security='apikey',
    params={'product_id': 'The product ID'}
)
class ImpactProductResource(Resource):
    """Resource for managing individual impact products."""

    @jwt_required()
    @impact_product_ns.doc(
        description='Get a specific impact product by ID'
    )
    @impact_product_ns.marshal_with(
        impact_product_model,
        code=200,
        description='Successfully retrieved the impact product'
    )
    def get(self, product_id: int) -> Dict[str, Any]:
        """
        Get a specific impact product.

        Args:
            product_id: The ID of the product to retrieve

        Returns:
            Dict containing the product information
        """
        try:
            product = ImpactProduct.query.get(product_id)
            if not product or product.is_deleted:
                impact_product_ns.abort(
                    404,
                    message='Product not found'
                )
            return product
        except Exception as e:
            current_app.logger.error(
                f'Error retrieving product {product_id}: {str(e)}'
            )
            impact_product_ns.abort(
                500,
                message='Internal server error'
            )

    @impact_product_ns.doc(security='Bearer Auth', responses={200: 'Updated', 404: 'Impact Product not found', 403: 'Unauthorized'})
    @jwt_required()
    @impact_product_ns.expect(impact_product_model, validate=True)
    def put(self, product_id: int) -> Dict[str, Any]:
        """
        Update an existing Impact Product (admin and manager only).

        Args:
            product_id: ID of the product to update

        Returns:
            Dictionary containing the updated product data
        """
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'manager'):
            return {'message': 'Unauthorized'}, 403

        product = ImpactProduct.query.filter_by(id=product_id, is_deleted=False).first()
        if not product:
            return {'message': 'Impact Product not found'}, 404

        data = request.json

        # Update product fields
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'category' in data:
            category = ProductCategory.query.filter_by(name=data['category']).first()
            if not category:
                return {'message': f"Category '{data['category']}' not found"}, 400
            product.category = category
        if 'group' in data:
            product.group = data['group']
        if 'status' in data:
            product.status = data['status']

        product.updated_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log the update to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='impact_product',
                resource_id=product.id,
                details=f"User updated Impact Product with ID {product.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return product.serialize()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating product: {e}")
            return {"message": "Error updating product"}, 500

    @impact_product_ns.doc(security='Bearer Auth', responses={200: 'Deleted', 404: 'Impact Product not found', 403: 'Unauthorized'})
    @jwt_required()
    def delete(self, product_id: int) -> Dict[str, Any]:
        """
        Soft-delete an Impact Product (admin only).

        Args:
            product_id: ID of the product to delete

        Returns:
            Dictionary containing success message
        """
        current_user = get_jwt_identity()

        # Role-based access control
        if not check_role_permission(current_user, 'admin'):
            return {'message': 'Unauthorized'}, 403

        product = ImpactProduct.query.filter_by(id=product_id, is_deleted=False).first()
        if not product:
            return {'message': 'Impact Product not found'}, 404

        product.is_deleted = True
        product.status = 'inactive'
        product.updated_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log the deletion to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='DELETE',
                resource_type='impact_product',
                resource_id=product.id,
                details=f"User deleted Impact Product with ID {product.id}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': 'Impact Product deleted successfully'}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting product: {e}")
            return {"message": "Error deleting product"}, 500
