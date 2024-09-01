from flask_restful import Resource
from flask import request, jsonify
from models.branch_model import Branch
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class BranchResource(Resource):
    @jwt_required()
    def get(self, branch_id=None):
        current_user = get_jwt_identity()
        if branch_id:
            branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
            if not branch:
                return {'message': 'Branch not found'}, 404
            return branch.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            branch_query = Branch.query.filter_by(is_deleted=False)

            if filter_by:
                branch_query = branch_query.filter(Branch.name.ilike(f'%{filter_by}%'))

            branches = branch_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            return {
                'branches': [branch.serialize() for branch in branches.items],
                'total': branches.total,
                'pages': branches.pages,
                'current_page': branches.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data = request.json

        # Validation of required fields
        if not data.get('name') or not data.get('address') or not data.get('city') or not data.get('region'):
            return {'message': 'Missing required fields'}, 400

        new_branch = Branch(
            name=data['name'],
            address=data['address'],
            city=data['city'],
            region=data['region'],
            ghpost_gps=data.get('ghpost_gps')
        )
        db.session.add(new_branch)
        db.session.commit()

        # Log creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='branch',
            resource_id=new_branch.id,
            details=f"Created branch with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_branch.serialize(), 201

    @jwt_required()
    def put(self, branch_id):
        current_user = get_jwt_identity()
        branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
        if not branch:
            return {'message': 'Branch not found'}, 404

        data = request.json
        branch.name = data.get('name', branch.name)
        branch.address = data.get('address', branch.address)
        branch.city = data.get('city', branch.city)
        branch.region = data.get('region', branch.region)
        branch.ghpost_gps = data.get('ghpost_gps', branch.ghpost_gps)
        branch.updated_at = datetime.utcnow()

        db.session.commit()

        # Log update to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Updated branch with details: {data}"
        )
        db.session.add(audit)
        db.session.commit()

        return branch.serialize(), 200

    @jwt_required()
    def delete(self, branch_id):
        current_user = get_jwt_identity()
        branch = Branch.query.filter_by(id=branch_id, is_deleted=False).first()
        if not branch:
            return {'message': 'Branch not found'}, 404

        branch.is_deleted = True
        db.session.commit()

        # Log deletion to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Deleted branch with id: {branch_id}"
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Branch deleted successfully'}, 200
