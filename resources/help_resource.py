from flask_restx import Namespace, Resource, fields
from flask import request
from app import db, logger
from models.help_model import HelpStep, HelpTour
from models.audit_model import AuditTrail
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

# Define a namespace for HelpTour and HelpStep related operations
help_ns = Namespace('help', description='Help Tour and Help Step operations')

# Define models for Swagger documentation
help_step_model = help_ns.model('HelpStep', {
    'id': fields.Integer(description='Help Step ID'),
    'page_name': fields.String(required=True, description='Name of the page'),
    'target': fields.String(required=True, description='Target element to highlight'),
    'content': fields.String(required=True, description='Content of the help step'),
    'order': fields.Integer(required=True, description='Order of the help step')
})

help_tour_model = help_ns.model('HelpTour', {
    'id': fields.Integer(description='Help Tour ID'),
    'user_id': fields.Integer(required=True, description='User ID'),
    'completed': fields.Boolean(description='Is Completed'),
    'completed_at': fields.String(description='Completed At'),
    'steps': fields.List(fields.Nested(help_step_model), description='List of Help Steps')
})

@help_ns.route('/steps')
class HelpStepResource(Resource):
    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    @help_ns.expect(help_step_model, validate=True)
    def post(self):
        """Create a new Help Step (Admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to create a Help Step.")
            return {'message': 'Unauthorized'}, 403

        data = request.json
        new_step = HelpStep(
            page_name=data['page_name'],
            target=data['target'],
            content=data['content'],
            order=data['order']
        )
        db.session.add(new_step)
        db.session.commit()

        logger.info(f"Created new help step with ID {new_step.id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='help_step',
            resource_id=new_step.id,
            details=f"Created Help Step with ID {new_step.id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return new_step.serialize(), 201

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Retrieve all Help Steps."""
        steps = HelpStep.query.order_by(HelpStep.order).all()
        logger.info("Retrieved all help steps.")

        # Log access to the audit trail
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='help_steps',
            resource_id=None,
            details="Accessed all Help Steps",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return [step.serialize() for step in steps], 200

@help_ns.route('/steps/<int:step_id>')
class SingleHelpStepResource(Resource):
    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self, step_id):
        """Retrieve a specific Help Step by ID."""
        step = HelpStep.query.get(step_id)
        if not step:
            logger.error(f"Help Step with ID {step_id} not found.")
            return {'message': 'Help Step not found'}, 404

        # Log access to the audit trail
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='help_step',
            resource_id=step.id,
            details=f"Accessed Help Step with ID {step_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return step.serialize(), 200

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    @help_ns.expect(help_step_model, validate=True)
    def put(self, step_id):
        """Update a specific Help Step (Admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to update Help Step {step_id}.")
            return {'message': 'Unauthorized'}, 403

        step = HelpStep.query.get(step_id)
        if not step:
            logger.error(f"Help Step with ID {step_id} not found.")
            return {'message': 'Help Step not found'}, 404

        data = request.json
        step.page_name = data.get('page_name', step.page_name)
        step.target = data.get('target', step.target)
        step.content = data.get('content', step.content)
        step.order = data.get('order', step.order)

        db.session.commit()
        logger.info(f"Updated Help Step with ID {step_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='UPDATE',
            resource_type='help_step',
            resource_id=step.id,
            details=f"Updated Help Step with ID {step_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return step.serialize(), 200

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, step_id):
        """Delete a Help Step (Admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to delete Help Step {step_id}.")
            return {'message': 'Unauthorized'}, 403

        step = HelpStep.query.get(step_id)
        if not step:
            logger.error(f"Help Step with ID {step_id} not found.")
            return {'message': 'Help Step not found'}, 404

        db.session.delete(step)
        db.session.commit()
        logger.info(f"Deleted Help Step with ID {step_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='help_step',
            resource_id=step.id,
            details=f"Deleted Help Step with ID {step_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Help Step deleted successfully'}, 200


@help_ns.route('/tours')
class HelpTourResource(Resource):
    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    @help_ns.expect(help_tour_model, validate=True)
    def post(self):
        """Create a new Help Tour."""
        new_tour = HelpTour(user_id=get_jwt_identity()['id'])
        db.session.add(new_tour)
        db.session.commit()

        logger.info(f"Created new help tour with ID {new_tour.id} for user ID {get_jwt_identity()['id']}.")
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='CREATE',
            resource_type='help_tour',
            resource_id=new_tour.id,
            details=f"Created Help Tour with ID {new_tour.id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return new_tour.serialize(), 201

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self):
        """Retrieve all Help Tours."""
        tours = HelpTour.query.all()
        logger.info("Retrieved all help tours.")

        # Log access to the audit trail
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='help_tours',
            resource_id=None,
            details="Accessed all Help Tours",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return [tour.serialize() for tour in tours], 200

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    @help_ns.param('page_name', 'Name of the page to fetch the Help Tour')
    def get(self):
        """Retrieve Help Tours by Page Name."""
        page_name = request.args.get('page_name')
        tours = HelpTour.query.filter(HelpTour.steps.any(HelpStep.page_name == page_name)).all()
        if not tours:
            logger.warning(f"No Help Tours found for page name: {page_name}")
            return {'message': 'No Help Tours found for the specified page name'}, 404

        logger.info(f"Retrieved {len(tours)} help tours for page name: {page_name}.")

        # Log access to the audit trail
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='help_tours',
            resource_id=None,
            details=f"Accessed Help Tours for page name: {page_name}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return [tour.serialize() for tour in tours], 200


@help_ns.route('/tours/<int:tour_id>')
class SingleHelpTourResource(Resource):
    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self, tour_id):
        """Retrieve a specific Help Tour by ID."""
        tour = HelpTour.query.get(tour_id)
        if not tour:
            logger.error(f"Help Tour with ID {tour_id} not found.")
            return {'message': 'Help Tour not found'}, 404

        # Log access to the audit trail
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='help_tour',
            resource_id=tour.id,
            details=f"Accessed Help Tour with ID {tour_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return tour.serialize(), 200

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def put(self, tour_id):
        """Mark Help Tour as completed."""
        tour = HelpTour.query.get(tour_id)
        if not tour:
            logger.error(f"Help Tour with ID {tour_id} not found.")
            return {'message': 'Help Tour not found'}, 404

        # Mark the tour as completed
        tour.completed = True
        tour.completed_at = datetime.utcnow()
        db.session.commit()
        logger.info(f"Marked Help Tour with ID {tour_id} as completed.")
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='UPDATE',
            resource_type='help_tour',
            resource_id=tour.id,
            details=f"Marked Help Tour with ID {tour_id} as completed",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return tour.serialize(), 200

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def delete(self, tour_id):
        """Delete a Help Tour (Admin only)."""
        current_user = get_jwt_identity()
        if current_user['role'].lower() != 'admin':
            logger.warning(f"Unauthorized attempt by User {current_user['id']} to delete Help Tour {tour_id}.")
            return {'message': 'Unauthorized'}, 403

        tour = HelpTour.query.get(tour_id)
        if not tour:
            logger.error(f"Help Tour with ID {tour_id} not found.")
            return {'message': 'Help Tour not found'}, 404

        db.session.delete(tour)
        db.session.commit()
        logger.info(f"Deleted Help Tour with ID {tour_id}.")
        audit = AuditTrail(
            user_id=current_user['id'],
            action='DELETE',
            resource_type='help_tour',
            resource_id=tour.id,
            details=f"Deleted Help Tour with ID {tour_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {'message': 'Help Tour deleted successfully'}, 200

@help_ns.route('/tours/<int:tour_id>/steps')
class HelpTourStepsResource(Resource):
    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    @help_ns.expect(help_step_model, validate=True)
    def post(self, tour_id):
        """Add a step to a Help Tour."""
        tour = HelpTour.query.get(tour_id)
        if not tour:
            logger.error(f"Help Tour with ID {tour_id} not found.")
            return {'message': 'Help Tour not found'}, 404

        data = request.json
        step = HelpStep.query.get(data['id'])
        if not step:
            logger.error(f"Help Step with ID {data['id']} not found.")
            return {'message': 'Help Step not found'}, 404

        tour.steps.append(step)
        db.session.commit()

        logger.info(f"Added Help Step with ID {step.id} to Help Tour with ID {tour_id}.")
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='UPDATE',
            resource_type='help_tour',
            resource_id=tour.id,
            details=f"Added Help Step with ID {step.id} to Help Tour with ID {tour_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return tour.serialize(), 200

    @help_ns.doc(security='Bearer Auth')
    @jwt_required()
    def get(self, tour_id):
        """Retrieve all steps for a Help Tour."""
        tour = HelpTour.query.get(tour_id)
        if not tour:
            logger.error(f"Help Tour with ID {tour_id} not found.")
            return {'message': 'Help Tour not found'}, 404

        # Log access to the audit trail
        audit = AuditTrail(
            user_id=get_jwt_identity()['id'],
            action='ACCESS',
            resource_type='help_tour_steps',
            resource_id=tour.id,
            details=f"Accessed steps for Help Tour with ID {tour_id}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()

        return {
            'tour_id': tour.id,
            'steps': [step.serialize() for step in tour.steps]
        }, 200
