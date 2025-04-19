from flask_restx import Namespace, Resource, fields, reqparse
from flask import request
from extensions import db
from models.help_model import HelpStep, HelpTour, HelpStepCategory
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from resources.auth_resource import admin_required
from typing import Dict, Any, List, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Define a namespace for HelpTour and HelpStep related operations
help_ns = Namespace('help', description='Help Tour and Help Step operations')

# Define models for Swagger documentation
help_step_model = help_ns.model('HelpStep', {
    'id': fields.Integer(description='Help Step ID'),
    'page_name': fields.String(required=True, description='Name of the page'),
    'target': fields.String(required=True, description='Target element to highlight'),
    'content': fields.String(required=True, description='Content of the help step'),
    'order': fields.Integer(required=True, description='Order of the help step'),
    'category': fields.String(description='Category of the help step'),
    'completed': fields.Boolean(description='Is the step completed'),
    'skipped': fields.Boolean(description='Was the step skipped')
})

help_tour_model = help_ns.model('HelpTour', {
    'id': fields.Integer(description='Help Tour ID'),
    'user_id': fields.Integer(required=True, description='User ID'),
    'name': fields.String(description='Tour name'),
    'description': fields.String(description='Tour description'),
    'completed': fields.Boolean(description='Is Completed'),
    'completed_at': fields.String(description='Completed At'),
    'last_step_completed': fields.Integer(description='Last completed step ID'),
    'steps': fields.List(fields.Nested(help_step_model), description='List of Help Steps')
})

@help_ns.route('/steps')
class HelpStepResource(Resource):
    """
    Resource for managing individual help steps.
    """
    @jwt_required()
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

    @jwt_required()
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

    @jwt_required()
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
    @jwt_required()
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

    @jwt_required()
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
    @jwt_required()
    def get(self) -> Dict[str, Any]:
        """
        Get a specific help tour by ID.
        """
        tour_id = request.args.get('tour_id')
        if not tour_id:
            return {'message': 'Tour ID is required'}, 400

        tour = HelpTour.query.get(tour_id)
        if not tour:
            return {'message': 'Tour not found'}, 404

        return tour.serialize()

    @jwt_required()
    @admin_required
    def put(self) -> Dict[str, Any]:
        """
        Update a specific help tour.
        """
        tour_id = request.args.get('tour_id')
        if not tour_id:
            return {'message': 'Tour ID is required'}, 400

        tour = HelpTour.query.get(tour_id)
        if not tour:
            return {'message': 'Tour not found'}, 404

        data = request.get_json()
        tour.update(data)
        db.session.commit()
        return tour.serialize()

    @jwt_required()
    @admin_required
    def delete(self) -> Dict[str, Any]:
        """
        Delete a specific help tour.
        """
        tour_id = request.args.get('tour_id')
        if not tour_id:
            return {'message': 'Tour ID is required'}, 400

        tour = HelpTour.query.get(tour_id)
        if not tour:
            return {'message': 'Tour not found'}, 404

        db.session.delete(tour)
        db.session.commit()
        return {'message': 'Tour deleted successfully'}


@help_ns.route('/tours/list')
class HelpTourListResource(Resource):
    """
    Resource for managing lists of help tours.
    """
    @jwt_required()
    def get(self) -> Dict[str, Any]:
        """
        Get all help tours with optional filtering.

        Returns:
            Dictionary containing list of help tours
        """
        parser = reqparse.RequestParser()
        parser.add_argument('userId', type=int, location='args')
        parser.add_argument('user_id', type=int, location='args')
        parser.add_argument('is_template', type=bool)
        parser.add_argument('include_deleted', type=bool, default=False)
        args = parser.parse_args()

        query = HelpTour.query
        if not args.get('include_deleted'):
            query = query.filter_by(is_deleted=False)

        user_id = args.get('userId') or args.get('user_id')
        if user_id:
            query = query.filter_by(user_id=user_id)

        if args.get('is_template') is not None:
            query = query.filter_by(is_template=args['is_template'])

        help_tours = query.all()
        return {'help_tours': [tour.serialize() for tour in help_tours]}

    @jwt_required()
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
    @jwt_required()
    @admin_required
    def get(self) -> Dict[str, Any]:
        """
        Get all help tour templates.

        Returns:
            Dictionary containing list of help tour templates
        """
        templates = HelpTour.get_templates()
        return {'templates': [template.serialize() for template in templates]}

    @jwt_required()
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


@help_ns.route('/tours/<int:tour_id>/steps/<int:step_id>/status')
class HelpStepStatusResource(Resource):
    """
    Resource for managing help step status.
    """
    @jwt_required()
    def get(self, tour_id: int, step_id: int) -> Dict[str, Any]:
        """
        Get status of a specific step in a help tour.

        Args:
            tour_id: ID of the help tour
            step_id: ID of the help step

        Returns:
            Dictionary containing step status
        """
        tour = HelpTour.query.get(tour_id)
        if not tour:
            return {'message': 'Help tour not found'}, 404

        status = tour.get_step_status(step_id)
        return status

    @jwt_required()
    def put(self, tour_id: int, step_id: int) -> Dict[str, Any]:
        """
        Update status of a specific step in a help tour.

        Args:
            tour_id: ID of the help tour
            step_id: ID of the help step

        Returns:
            Dictionary containing success message
        """
        tour = HelpTour.query.get(tour_id)
        if not tour:
            return {'message': 'Help tour not found'}, 404

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        try:
            if data.get('completed'):
                success = tour.mark_step_completed(step_id)
            elif data.get('skipped'):
                success = tour.mark_step_skipped(step_id)
            else:
                return {'message': 'Invalid status update'}, 400

            if success:
                return {'message': 'Step status updated successfully'}
            else:
                return {'message': 'Failed to update step status'}, 500
        except Exception as e:
            logger.error(f"Error updating step status: {e}")
            return {'message': 'Error updating step status'}, 500

@help_ns.route('/tours/<int:tour_id>/reset')
class HelpTourResetResource(Resource):
    """
    Resource for resetting help tours.
    """
    @jwt_required()
    def post(self, tour_id: int) -> Dict[str, Any]:
        """
        Reset a help tour to its initial state.

        Args:
            tour_id: ID of the help tour to reset

        Returns:
            Dictionary containing success message
        """
        tour = HelpTour.query.get(tour_id)
        if not tour:
            return {'message': 'Help tour not found'}, 404

        try:
            success = HelpTour.reset_user_help_tour(tour.user_id)
            if success:
                return {'message': 'Help tour reset successfully'}
            else:
                return {'message': 'Failed to reset help tour'}, 500
        except Exception as e:
            logger.error(f"Error resetting help tour: {e}")
            return {'message': 'Error resetting help tour'}, 500

@help_ns.route('/tours/progress')
class HelpTourProgressResource(Resource):
    """
    Resource for getting help tour progress.
    """
    @jwt_required()
    def get(self) -> Dict[str, Any]:
        """
        Get progress of the current user's help tour.

        Returns:
            Dictionary containing progress information
        """
        user_id = get_jwt_identity()
        if not user_id:
            return {'message': 'User ID not found'}, 400

        progress = HelpTour.get_help_tour_progress(user_id)
        return progress
