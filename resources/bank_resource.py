from flask_restx import Namespace, Resource, fields
from flask import request
from models.bank_model import Bank, BankBranch
from models.audit_model import AuditTrail
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_client_ip

# Create a namespace for bank-related operations
bank_ns = Namespace('banks', description='Operations related to banks and their branches')

# Define models for Swagger documentation
bank_branch_model = bank_ns.model('BankBranch', {
    'id': fields.Integer(description='Branch ID'),
    'name': fields.String(required=True, description='Branch Name'),
    'code': fields.String(description='Branch Code/Identifier'),
    'sort_code': fields.String(description='Branch Sort Code'),
    'address': fields.String(description='Branch Address'),
    'city': fields.String(description='Branch City'),
    'region': fields.String(description='Branch Region'),
    'country': fields.String(description='Branch Country'),
    'latitude': fields.Float(description='Branch Latitude'),
    'longitude': fields.Float(description='Branch Longitude'),
    'contact_phone': fields.String(description='Branch Contact Phone'),
    'contact_email': fields.String(description='Branch Contact Email'),
    'is_deleted': fields.Boolean(description='Soft delete flag')
})

bank_model = bank_ns.model('Bank', {
    'id': fields.Integer(description='Bank ID'),
    'name': fields.String(required=True, description='Bank Name'),
    'code': fields.String(description='Bank Code (SWIFT/BIC)'),
    'website': fields.String(description='Bank Website'),
    'contact_email': fields.String(description='Bank Contact Email'),
    'contact_phone': fields.String(description='Bank Contact Phone'),
    'logo_url': fields.String(description='Bank Logo URL'),
    'bank_type': fields.String(description='Bank Type (Commercial, Development, etc.)'),
    'is_deleted': fields.Boolean(description='Soft delete flag'),
    'created_at': fields.DateTime(description='Creation date'),
    'updated_at': fields.DateTime(description='Last update date'),
    'bank_branches': fields.List(fields.Nested(bank_branch_model))
})

@bank_ns.route('/')
class BankResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.response(200, 'Success', [bank_model])
    @bank_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @bank_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @bank_ns.param('bank_type', 'Filter by bank type', type='string')
    @bank_ns.param('search', 'Search query for bank name', type='string')
    @jwt_required()
    def get(self):
        """Get all active banks along with their active branches."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        bank_type = request.args.get('bank_type')
        search_query = request.args.get('search')

        try:
            if search_query:
                banks = Bank.search_banks(search_query, bank_type)
            else:
                banks = Bank.get_active_banks(page, per_page)
            logger.info(f"Banks retrieved successfully by user ID {get_jwt_identity()}")
            return [bank.serialize() for bank in banks], 200
        except Exception as e:
            logger.error(f"Error retrieving banks: {e}")
            return {'message': 'Error retrieving banks'}, 500

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_model, validate=True)
    @jwt_required()
    def post(self):
        """Create a new bank."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(f"Unauthorized attempt to create bank by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_bank = Bank(
            name=data['name'],
            code=data.get('code'),
            website=data.get('website'),
            contact_email=data.get('contact_email'),
            contact_phone=data.get('contact_phone'),
            logo_url=data.get('logo_url'),
            bank_type=data.get('bank_type')
        )
        db.session.add(new_bank)
        db.session.commit()

        # Log the creation in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='bank',
            resource_id=new_bank.id,
            details=f"Bank '{new_bank.name}' created",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Bank '{new_bank.name}' created successfully by admin ID {current_user['id']}")
        return {'message': 'Bank created successfully', 'bank': new_bank.serialize()}, 201


@bank_ns.route('/<int:bank_id>')
class SingleBankResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.response(200, 'Success', bank_model)
    @jwt_required()
    def get(self, bank_id):
        """Get a single bank by its ID."""
        bank = Bank.query.filter_by(id=bank_id, is_deleted=False).first()

        if not bank:
            logger.error(f"Bank ID {bank_id} not found")
            return {'message': 'Bank not found'}, 404

        logger.info(f"Bank ID {bank_id} retrieved successfully by user ID {get_jwt_identity()}")
        return bank.serialize(), 200

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_model, validate=True)
    @jwt_required()
    def put(self, bank_id):
        """Update an existing bank."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(f"Unauthorized attempt to update bank by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        bank = Bank.query.filter_by(id=bank_id, is_deleted=False).first()

        if not bank:
            logger.error(f"Bank ID {bank_id} not found for update")
            return {'message': 'Bank not found'}, 404

        data = request.json
        bank.name = data['name']
        bank.code = data.get('code', bank.code)
        bank.website = data.get('website', bank.website)
        bank.contact_email = data.get('contact_email', bank.contact_email)
        bank.contact_phone = data.get('contact_phone', bank.contact_phone)
        bank.logo_url = data.get('logo_url', bank.logo_url)
        bank.bank_type = data.get('bank_type', bank.bank_type)
        db.session.commit()

        # Log the update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='bank',
            resource_id=bank.id,
            details=f"Bank '{bank.name}' updated",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Bank '{bank.name}' updated successfully by admin ID {current_user['id']}")
        return {'message': 'Bank updated successfully', 'bank': bank.serialize()}, 200

    @bank_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, bank_id):
        """Soft delete a bank."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt to delete bank by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        bank = Bank.query.filter_by(id=bank_id).first()

        if not bank:
            logger.error(f"Bank ID {bank_id} not found for deletion")
            return {'message': 'Bank not found'}, 404

        bank.is_deleted = True
        db.session.commit()

        # Log the deletion in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='bank',
            resource_id=bank.id,
            details=f"Bank '{bank.name}' soft deleted",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Bank '{bank.name}' deleted successfully by admin ID {current_user['id']}")
        return {'message': 'Bank deleted successfully'}, 200


@bank_ns.route('/bank-branches')
class BankBranchResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.param('page', 'Page number for pagination', type='integer', default=1)
    @bank_ns.param('per_page', 'Number of items per page', type='integer', default=10)
    @bank_ns.param('bank_id', 'Filter by bank ID', type='integer')
    @bank_ns.param('city', 'Filter by city', type='string')
    @bank_ns.param('search', 'Search query for branch name', type='string')
    @jwt_required()
    def get(self):
        """Get all active bank branches with optional filters."""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        bank_id = request.args.get('bank_id', type=int)
        city = request.args.get('city')
        search_query = request.args.get('search')

        try:
            if search_query:
                branches = BankBranch.search_branches(search_query, bank_id, city)
            else:
                branches = BankBranch.get_active_branches(page, per_page)
            logger.info(f"Branches retrieved successfully by user ID {get_jwt_identity()}")
            return [branch.serialize() for branch in branches], 200
        except Exception as e:
            logger.error(f"Error retrieving branches: {e}")
            return {'message': 'Error retrieving branches'}, 500

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_branch_model, validate=True)
    @jwt_required()
    def post(self):
        """Create a new branch."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(f"Unauthorized attempt to create branch by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_branch = BankBranch(
            name=data['name'],
            code=data.get('code'),
            bank_id=data['bank_id'],
            sort_code=data.get('sort_code'),
            address=data.get('address'),
            city=data.get('city'),
            region=data.get('region'),
            country=data.get('country'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            contact_phone=data.get('contact_phone'),
            contact_email=data.get('contact_email')
        )
        db.session.add(new_branch)
        db.session.commit()

        # Log the creation in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='branch',
            resource_id=new_branch.id,
            details=f"Branch '{new_branch.name}' created",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch '{new_branch.name}' created successfully by admin ID {current_user['id']}")
        return {'message': 'Branch created successfully', 'branch': new_branch.serialize()}, 201


@bank_ns.route('/bank-branches/<int:branch_id>')
class SingleBranchResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.response(200, 'Success', bank_branch_model)
    @jwt_required()
    def get(self, branch_id):
        """Get a single branch by its ID."""
        branch = BankBranch.query.filter_by(id=branch_id, is_deleted=False).first()

        if not branch:
            logger.error(f"Branch ID {branch_id} not found")
            return {'message': 'Branch not found'}, 404

        logger.info(f"Branch ID {branch_id} retrieved successfully by user ID {get_jwt_identity()}")
        return branch.serialize(), 200

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_branch_model, validate=True)
    @jwt_required()
    def put(self, branch_id):
        """Update an existing branch."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() not in ['admin', 'manager']:
            logger.warning(f"Unauthorized attempt to update branch by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        branch = BankBranch.query.filter_by(id=branch_id, is_deleted=False).first()

        if not branch:
            logger.error(f"Branch ID {branch_id} not found for update")
            return {'message': 'Branch not found'}, 404

        data = request.json
        branch.name = data['name']
        branch.code = data.get('code', branch.code)
        branch.sort_code = data.get('sort_code', branch.sort_code)
        branch.address = data.get('address', branch.address)
        branch.city = data.get('city', branch.city)
        branch.region = data.get('region', branch.region)
        branch.country = data.get('country', branch.country)
        branch.latitude = data.get('latitude', branch.latitude)
        branch.longitude = data.get('longitude', branch.longitude)
        branch.contact_phone = data.get('contact_phone', branch.contact_phone)
        branch.contact_email = data.get('contact_email', branch.contact_email)
        db.session.commit()

        # Log the update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Branch '{branch.name}' updated",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch '{branch.name}' updated successfully by admin ID {current_user['id']}")
        return {'message': 'Branch updated successfully', 'branch': branch.serialize()}, 200

    @bank_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, branch_id):
        """Soft delete a branch."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt to delete branch by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        branch = BankBranch.query.filter_by(id=branch_id).first()

        if not branch:
            logger.error(f"Branch ID {branch_id} not found for deletion")
            return {'message': 'Branch not found'}, 404

        branch.is_deleted = True
        db.session.commit()

        # Log the deletion in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Branch '{branch.name}' soft deleted",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch '{branch.name}' deleted successfully by admin ID {current_user['id']}")
        return {'message': 'Branch deleted successfully'}, 200
