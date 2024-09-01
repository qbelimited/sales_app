from flask_restful import Resource
from flask import request, jsonify
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class ImpactProductResource(Resource):
    @jwt_required()
    def get(self, product_id=None):
        current_user = get_jwt_identity()
        if product_id:
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
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            product_query = ImpactProduct.query.filter_by(is_deleted=False)

            if filter_by:
                product_query = product_query.filter(ImpactProduct.name.ilike(f'%{filter_by}%'))

            products = product_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='impact_product_list',
                resource_id=None,
                details=f"User accessed list of Impact Products"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'products': [product.serialize() for product in products.items],
                'total': products.total,
                'pages': products.pages,
                'current_page': products.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data = request.json

        new_product = ImpactProduct(
            name=data['name'],
            category=data['category']
        )
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

    @jwt_required()
    def put(self, product_id):
        current_user = get_jwt_identity()
        product = ImpactProduct.query.filter_by(id=product_id, is_deleted=False).first()
        if not product:
            return {'message': 'Impact Product not found'}, 404

        data = request.json
        product.name = data.get('name', product.name)
        product.category = data.get('category', product.category)
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

    @jwt_required()
    def delete(self, product_id):
        current_user = get_jwt_identity()
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
