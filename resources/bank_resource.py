from flask_restx import Namespace, Resource, fields
from flask import request
from models.bank_model import Bank, BankBranch
from models.audit_model import AuditTrail
from app import db, logger  # Import logger from app.py
from flask_jwt_extended import jwt_required, get_jwt_identity

# Create a namespace for bank-related operations
bank_ns = Namespace('banks', description='Operations related to banks and their branches')

# Define models for Swagger documentation
bank_model = bank_ns.model('Bank', {
    'id': fields.Integer(description='Bank ID'),
    'name': fields.String(required=True, description='Bank Name'),
    'is_deleted': fields.Boolean(description='Soft delete flag'),
    'created_at': fields.DateTime(description='Creation date'),
    'updated_at': fields.DateTime(description='Last update date'),
    'bank_branches': fields.List(fields.Nested(bank_ns.model('BankBranch', {
        'id': fields.Integer(description='Branch ID'),
        'name': fields.String(required=True, description='Branch Name'),
        'sort_code': fields.String(description='Branch Sort Code'),
        'is_deleted': fields.Boolean(description='Soft delete flag')
    })))
})

@bank_ns.route('/')
class BankResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.response(200, 'Success', [bank_model])
    @jwt_required()
    def get(self):
        """Get all active banks along with their active branches."""
        banks = Bank.get_active_banks()
        logger.info(f"Banks retrieved successfully by user ID {get_jwt_identity()['id']}")
        return [bank.serialize() for bank in banks], 200

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_model, validate=True)
    @jwt_required()
    def post(self):
        """Create a new bank."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to create bank by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_bank = Bank(name=data['name'])
        db.session.add(new_bank)
        db.session.commit()

        # Log the creation in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='bank',
            resource_id=new_bank.id,
            details=f"Bank '{new_bank.name}' created"
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

        logger.info(f"Bank ID {bank_id} retrieved successfully by user ID {get_jwt_identity()['id']}")
        return bank.serialize(), 200

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_model, validate=True)
    @jwt_required()
    def put(self, bank_id):
        """Update an existing bank."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to update bank by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        bank = Bank.query.filter_by(id=bank_id, is_deleted=False).first()

        if not bank:
            logger.error(f"Bank ID {bank_id} not found for update")
            return {'message': 'Bank not found'}, 404

        data = request.json
        bank.name = data['name']
        db.session.commit()

        # Log the update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='bank',
            resource_id=bank.id,
            details=f"Bank '{bank.name}' updated"
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
        if current_user['role'] != 'admin':
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
            details=f"Bank '{bank.name}' soft deleted"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Bank '{bank.name}' deleted successfully by admin ID {current_user['id']}")
        return {'message': 'Bank deleted successfully'}, 200


@bank_ns.route('/branches')
class BankBranchResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Get all active bank branches."""
        branches = BankBranch.get_active_branches()
        logger.info(f"Branches retrieved successfully by user ID {get_jwt_identity()['id']}")
        return [branch.serialize() for branch in branches], 200

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_model, validate=True)
    @jwt_required()
    def post(self):
        """Create a new branch."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to create branch by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_branch = BankBranch(
            name=data['name'],
            bank_id=data['bank_id'],
            sort_code=data.get('sort_code')
        )
        db.session.add(new_branch)
        db.session.commit()

        # Log the creation in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='branch',
            resource_id=new_branch.id,
            details=f"Branch '{new_branch.name}' created"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch '{new_branch.name}' created successfully by admin ID {current_user['id']}")
        return {'message': 'Branch created successfully', 'branch': new_branch.serialize()}, 201


@bank_ns.route('/branches/<int:branch_id>')
class SingleBranchResource(Resource):
    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.response(200, 'Success', bank_model)
    @jwt_required()
    def get(self, branch_id):
        """Get a single branch by its ID."""
        branch = BankBranch.query.filter_by(id=branch_id, is_deleted=False).first()

        if not branch:
            logger.error(f"Branch ID {branch_id} not found")
            return {'message': 'Branch not found'}, 404

        logger.info(f"Branch ID {branch_id} retrieved successfully by user ID {get_jwt_identity()['id']}")
        return branch.serialize(), 200

    @bank_ns.doc(security='Bearer Auth')
    @bank_ns.expect(bank_model, validate=True)
    @jwt_required()
    def put(self, branch_id):
        """Update an existing branch."""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            logger.warning(f"Unauthorized attempt to update branch by user ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        branch = BankBranch.query.filter_by(id=branch_id, is_deleted=False).first()

        if not branch:
            logger.error(f"Branch ID {branch_id} not found for update")
            return {'message': 'Branch not found'}, 404

        data = request.json
        branch.name = data['name']
        branch.sort_code = data.get('sort_code', branch.sort_code)
        db.session.commit()

        # Log the update in the audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='branch',
            resource_id=branch.id,
            details=f"Branch '{branch.name}' updated"
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
        if current_user['role'] != 'admin':
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
            details=f"Branch '{branch.name}' soft deleted"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(f"Branch '{branch.name}' deleted successfully by admin ID {current_user['id']}")
        return {'message': 'Branch deleted successfully'}, 200
