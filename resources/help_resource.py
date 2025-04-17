from flask_restx import Namespace, Resource, fields
from flask import request
from app import db, logger
from models.help_model import HelpStep, HelpTour, HelpStepCategory, HelpStepLanguage
from models.audit_model import AuditTrail
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from flask_restful import Resource, reqparse
from resources.auth_resource import token_required, admin_required
from typing import Dict, Any, List, Optional

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
    """
    Resource for managing individual help steps.
    """
    @token_required
    @admin_required
    def get(self, step_id: int) -> Dict[str, Any]:
        """
        Get a specific help step by ID.

        Args:
            step_id: ID of the help step to retrieve

        Returns:
            Dictionary containing help step data
        """
        help_step = HelpStep.query.get(step_id)
        if not help_step or help_step.is_deleted:
            return {'message': 'Help step not found'}, 404
        return help_step.serialize()

    @token_required
    @admin_required
    def put(self, step_id: int) -> Dict[str, Any]:
        """
        Update a specific help step.

        Args:
            step_id: ID of the help step to update

        Returns:
            Dictionary containing updated help step data
        """
        help_step = HelpStep.query.get(step_id)
        if not help_step or help_step.is_deleted:
            return {'message': 'Help step not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('page_name', type=str)
        parser.add_argument('target', type=str)
        parser.add_argument('content', type=str)
        parser.add_argument('order', type=int)
        parser.add_argument('category', type=str)
        args = parser.parse_args()

        for key, value in args.items():
            if value is not None:
                setattr(help_step, key, value)

        try:
            db.session.commit()
            logger.info(f"Updated help step: {step_id}")
            return help_step.serialize()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating help step {step_id}: {e}")
            return {'message': 'Error updating help step'}, 500

    @token_required
    @admin_required
    def delete(self, step_id: int) -> Dict[str, Any]:
        """
        Soft delete a help step.

        Args:
            step_id: ID of the help step to delete

        Returns:
            Dictionary containing success message
        """
        help_step = HelpStep.query.get(step_id)
        if not help_step or help_step.is_deleted:
            return {'message': 'Help step not found'}, 404

        help_step.is_deleted = True
        try:
            db.session.commit()
            logger.info(f"Deleted help step: {step_id}")
            return {'message': 'Help step deleted successfully'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting help step {step_id}: {e}")
            return {'message': 'Error deleting help step'}, 500


class HelpStepListResource(Resource):
    """
    Resource for managing lists of help steps.
    """
    @token_required
    @admin_required
    def get(self) -> Dict[str, Any]:
        """
        Get all help steps with optional filtering.

        Returns:
            Dictionary containing list of help steps
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page_name', type=str)
        parser.add_argument('category', type=str)
        parser.add_argument('include_deleted', type=bool, default=False)
        args = parser.parse_args()

        query = HelpStep.query
        if not args.get('include_deleted'):
            query = query.filter_by(is_deleted=False)
        if args.get('page_name'):
            query = query.filter_by(page_name=args['page_name'])
        if args.get('category'):
            query = query.filter_by(category=args['category'])

        help_steps = query.order_by(HelpStep.order).all()
        return {'help_steps': [step.serialize() for step in help_steps]}

    @token_required
    @admin_required
    def post(self) -> Dict[str, Any]:
        """
        Create a new help step.

        Returns:
            Dictionary containing created help step data
        """
        parser = reqparse.RequestParser()
        parser.add_argument('page_name', type=str, required=True)
        parser.add_argument('target', type=str, required=True)
        parser.add_argument('content', type=str, required=True)
        parser.add_argument('order', type=int, required=True)
        parser.add_argument('category', type=str,
                          default=HelpStepCategory.FEATURE.value)
        args = parser.parse_args()

        help_step = HelpStep(**args)
        try:
            db.session.add(help_step)
            db.session.commit()
            logger.info(f"Created new help step: {help_step.id}")
            return help_step.serialize()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating help step: {e}")
            return {'message': 'Error creating help step'}, 500


@help_ns.route('/tours')
class HelpTourResource(Resource):
    """
    Resource for managing individual help tours.
    """
    @token_required
    def get(self, tour_id: int) -> Dict[str, Any]:
        """
        Get a specific help tour by ID.

        Args:
            tour_id: ID of the help tour to retrieve

        Returns:
            Dictionary containing help tour data
        """
        help_tour = HelpTour.query.get(tour_id)
        if not help_tour or help_tour.is_deleted:
            return {'message': 'Help tour not found'}, 404
        return help_tour.serialize()

    @token_required
    @admin_required
    def put(self, tour_id: int) -> Dict[str, Any]:
        """
        Update a specific help tour.

        Args:
            tour_id: ID of the help tour to update

        Returns:
            Dictionary containing updated help tour data
        """
        help_tour = HelpTour.query.get(tour_id)
        if not help_tour or help_tour.is_deleted:
            return {'message': 'Help tour not found'}, 404

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('is_template', type=bool)
        args = parser.parse_args()

        for key, value in args.items():
            if value is not None:
                setattr(help_tour, key, value)

        try:
            db.session.commit()
            logger.info(f"Updated help tour: {tour_id}")
            return help_tour.serialize()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating help tour {tour_id}: {e}")
            return {'message': 'Error updating help tour'}, 500

    @token_required
    @admin_required
    def delete(self, tour_id: int) -> Dict[str, Any]:
        """
        Soft delete a help tour.

        Args:
            tour_id: ID of the help tour to delete

        Returns:
            Dictionary containing success message
        """
        help_tour = HelpTour.query.get(tour_id)
        if not help_tour or help_tour.is_deleted:
            return {'message': 'Help tour not found'}, 404

        help_tour.is_deleted = True
        try:
            db.session.commit()
            logger.info(f"Deleted help tour: {tour_id}")
            return {'message': 'Help tour deleted successfully'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting help tour {tour_id}: {e}")
            return {'message': 'Error deleting help tour'}, 500


class HelpTourListResource(Resource):
    """
    Resource for managing lists of help tours.
    """
    @token_required
    @admin_required
    def get(self) -> Dict[str, Any]:
        """
        Get all help tours with optional filtering.

        Returns:
            Dictionary containing list of help tours
        """
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=int)
        parser.add_argument('is_template', type=bool)
        parser.add_argument('include_deleted', type=bool, default=False)
        args = parser.parse_args()

        query = HelpTour.query
        if not args.get('include_deleted'):
            query = query.filter_by(is_deleted=False)
        if args.get('user_id'):
            query = query.filter_by(user_id=args['user_id'])
        if args.get('is_template') is not None:
            query = query.filter_by(is_template=args['is_template'])

        help_tours = query.all()
        return {'help_tours': [tour.serialize() for tour in help_tours]}

    @token_required
    @admin_required
    def post(self) -> Dict[str, Any]:
        """
        Create a new help tour.

        Returns:
            Dictionary containing created help tour data
        """
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=int, required=True)
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('description', type=str)
        parser.add_argument('is_template', type=bool, default=False)
        parser.add_argument('step_ids', type=list, location='json',
                          required=True)
        args = parser.parse_args()

        help_tour = HelpTour(
            user_id=args['user_id'],
            name=args['name'],
            description=args.get('description'),
            is_template=args['is_template']
        )

        steps = HelpStep.query.filter(HelpStep.id.in_(args['step_ids'])).all()
        help_tour.steps = steps

        try:
            db.session.add(help_tour)
            db.session.commit()
            logger.info(f"Created new help tour: {help_tour.id}")
            return help_tour.serialize()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating help tour: {e}")
            return {'message': 'Error creating help tour'}, 500


class HelpTourTemplateResource(Resource):
    """
    Resource for managing help tour templates.
    """
    @token_required
    @admin_required
    def get(self) -> Dict[str, Any]:
        """
        Get all help tour templates.

        Returns:
            Dictionary containing list of help tour templates
        """
        templates = HelpTour.get_templates()
        return {'templates': [template.serialize() for template in templates]}

    @token_required
    def post(self) -> Dict[str, Any]:
        """
        Create a new help tour from a template.

        Returns:
            Dictionary containing created help tour data
        """
        parser = reqparse.RequestParser()
        parser.add_argument('template_id', type=int, required=True)
        parser.add_argument('user_id', type=int, required=True)
        args = parser.parse_args()

        help_tour = HelpTour.create_from_template(args['template_id'],
                                                args['user_id'])
        if not help_tour:
            return {'message': 'Template not found'}, 404

        return help_tour.serialize()


class HelpTourProgressResource(Resource):
    """
    Resource for managing help tour progress.
    """
    @token_required
    def get(self, user_id: int) -> Dict[str, Any]:
        """
        Get help tour progress for a specific user.

        Args:
            user_id: ID of the user to get progress for

        Returns:
            Dictionary containing help tour progress data
        """
        progress = HelpTour.get_help_tour_progress(user_id)
        return progress

    @token_required
    def post(self, user_id: int) -> Dict[str, Any]:
        """
        Mark a help tour as completed for a specific user.

        Args:
            user_id: ID of the user to mark as completed

        Returns:
            Dictionary containing updated help tour data
        """
        help_tour = HelpTour.get_user_help_tour_status(user_id)
        if not help_tour:
            return {'message': 'Help tour not found'}, 404

        help_tour.completed = True
        help_tour.completed_at = datetime.utcnow()

        try:
            db.session.commit()
            logger.info(f"Marked help tour as completed for user: {user_id}")
            return help_tour.serialize()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking help tour as completed for user {user_id}: {e}")
            return {'message': 'Error marking help tour as completed'}, 500

    @token_required
    def delete(self, user_id: int) -> Dict[str, Any]:
        """
        Reset help tour progress for a specific user.

        Args:
            user_id: ID of the user to reset progress for

        Returns:
            Dictionary containing success message
        """
        help_tour = HelpTour.reset_user_help_tour(user_id)
        if not help_tour:
            return {'message': 'Help tour not found'}, 404

        return {'message': 'Help tour progress reset successfully'}
