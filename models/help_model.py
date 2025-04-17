from app import db, logger
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from sqlalchemy import and_
from sqlalchemy.orm import validates

# Association table for many-to-many relationship between HelpTour and HelpStep
help_tour_steps = db.Table(
    'help_tour_steps',
    db.Column('help_tour_id', db.Integer, db.ForeignKey('help_tour.id', ondelete='CASCADE'), primary_key=True),
    db.Column('help_step_id', db.Integer, db.ForeignKey('help_step.id', ondelete='CASCADE'), primary_key=True)
)


class HelpStep(db.Model):
    """
    Model representing a single step in a help tour.
    Each step is associated with a specific page and target element.
    """
    __tablename__ = 'help_step'

    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(100), nullable=False, index=True)
    target = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('page_name', 'order', name='uq_page_order'),
        db.Index('idx_help_step_page_order', 'page_name', 'order'),
    )

    @validates('page_name', 'target', 'content')
    def validate_fields(
        self,
        key: str,
        value: str
    ) -> str:
        """
        Validate help step fields.

        Args:
            key: Field name being validated
            value: Value to validate

        Returns:
            Validated and formatted value

        Raises:
            ValueError: If validation fails
        """
        if not value or not value.strip():
            raise ValueError(f"{key} cannot be empty")

        value = value.strip()

        if key == 'page_name' and len(value) > 100:
            raise ValueError("Page name cannot exceed 100 characters")
        elif key == 'target' and len(value) > 255:
            raise ValueError("Target cannot exceed 255 characters")

        return value

    def serialize(self) -> Dict[str, Any]:
        """Serialize help step data for API responses."""
        return {
            'id': self.id,
            'page_name': self.page_name,
            'target': self.target,
            'content': self.content,
            'order': self.order,
        }

    @staticmethod
    def get_steps_by_page(
        page_name: str,
        include_deleted: bool = False
    ) -> List['HelpStep']:
        """
        Retrieve all help steps for a specific page.

        Args:
            page_name: Name of the page to get steps for
            include_deleted: Whether to include deleted steps

        Returns:
            List of help steps for the page
        """
        query = HelpStep.query.filter_by(page_name=page_name)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.order_by(HelpStep.order).all()


class HelpTour(db.Model):
    """
    Model representing a user's help tour progress.
    Tracks which steps have been completed and when.
    """
    __tablename__ = 'help_tour'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    steps = db.relationship(
        'HelpStep',
        secondary=help_tour_steps,
        backref='help_tours',
        lazy='selectin'
    )
    user = db.relationship('User', backref='help_tours')

    def serialize(self) -> Dict[str, Any]:
        """Serialize help tour data for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'steps': [step.serialize() for step in self.steps.all()]
        }

    @staticmethod
    def get_user_help_tour_status(user_id: int) -> Optional['HelpTour']:
        """
        Retrieve the help tour status for a specific user.

        Args:
            user_id: ID of the user to get status for

        Returns:
            HelpTour object if found, None otherwise
        """
        help_tour = HelpTour.query.filter_by(user_id=user_id).first()
        logger.info(f"Retrieved help tour status for user_id: {user_id} - {help_tour}")
        return help_tour

    @staticmethod
    def set_user_help_tour_completed(user_id: int) -> 'HelpTour':
        """
        Mark the Help Tour as completed for a specific user.

        Args:
            user_id: ID of the user to mark as completed

        Returns:
            Updated or created HelpTour object

        Raises:
            IntegrityError: If database constraints are violated
            Exception: For other database errors
        """
        help_tour = HelpTour.get_user_help_tour_status(user_id)
        try:
            if help_tour:
                help_tour.completed = True
                help_tour.completed_at = datetime.utcnow()
                logger.info(f"Marked existing help tour as completed for user_id: {user_id}")
            else:
                help_tour = HelpTour(
                    user_id=user_id,
                    completed=True,
                    completed_at=datetime.utcnow()
                )
                db.session.add(help_tour)
                logger.info(f"Created new help tour for user_id: {user_id}")

            db.session.commit()
            logger.info(f"Successfully committed help tour status for user_id: {user_id}")
            return help_tour
        except IntegrityError as ie:
            db.session.rollback()
            logger.error(f"Integrity error while setting help tour completed for user_id: {user_id} - {ie}")
            raise
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error while setting help tour completed for user_id: {user_id} - {e}")
            raise

    @staticmethod
    def reset_user_help_tour(user_id: int) -> Optional['HelpTour']:
        """
        Reset the help tour progress for a specific user.

        Args:
            user_id: ID of the user to reset tour for

        Returns:
            Updated HelpTour object or None if not found
        """
        try:
            help_tour = HelpTour.get_user_help_tour_status(user_id)
            if help_tour:
                help_tour.completed = False
                help_tour.completed_at = None
                db.session.commit()
                logger.info(f"Reset help tour for user_id: {user_id}")
            return help_tour
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting help tour for user_id: {user_id} - {e}")
            return None

    @staticmethod
    def get_help_tour_progress(user_id: int) -> Dict[str, Any]:
        """
        Get detailed progress of a user's help tour.

        Args:
            user_id: ID of the user to get progress for

        Returns:
            Dictionary containing progress information
        """
        help_tour = HelpTour.get_user_help_tour_status(user_id)
        if not help_tour:
            return {
                'completed': False,
                'total_steps': 0,
                'completed_steps': 0,
                'progress_percentage': 0
            }

        total_steps = len(help_tour.steps)
        completed_steps = sum(1 for step in help_tour.steps if step.completed)
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return {
            'completed': help_tour.completed,
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'progress_percentage': progress_percentage
        }
