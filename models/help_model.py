from extensions import db
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import validates
from enum import Enum

class HelpStepCategory(Enum):
    INTRODUCTION = 'introduction'
    NAVIGATION = 'navigation'
    FEATURE = 'feature'
    TROUBLESHOOTING = 'troubleshooting'
    BEST_PRACTICES = 'best_practices'

# Association table for many-to-many relationship between HelpTour and HelpStep
help_tour_steps = db.Table(
    'help_tour_steps',
    db.Column('help_tour_id', db.Integer, db.ForeignKey('help_tour.id', ondelete='CASCADE'), primary_key=True),
    db.Column('help_step_id', db.Integer, db.ForeignKey('help_step.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for help step dependencies
help_step_dependencies = db.Table(
    'help_step_dependencies',
    db.Column('step_id', db.Integer, db.ForeignKey('help_step.id', ondelete='CASCADE'), primary_key=True),
    db.Column('dependency_id', db.Integer, db.ForeignKey('help_step.id', ondelete='CASCADE'), primary_key=True)
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
    category = db.Column(db.String(50), nullable=False, default=HelpStepCategory.FEATURE.value)
    version = db.Column(db.Integer, nullable=False, default=1)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    dependencies = db.relationship(
        'HelpStep',
        secondary=help_step_dependencies,
        primaryjoin=(help_step_dependencies.c.step_id == id),
        secondaryjoin=(help_step_dependencies.c.dependency_id == id),
        backref=db.backref('dependent_steps', lazy='dynamic')
    )

    __table_args__ = (
        db.UniqueConstraint('page_name', 'order', name='uq_page_order'),
        db.Index('idx_help_step_page_order', 'page_name', 'order'),
        db.Index('idx_help_step_category', 'category'),
    )

    @validates('page_name', 'target', 'content', 'category')
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
        elif key == 'category' and value not in [cat.value for cat in HelpStepCategory]:
            raise ValueError(f"Invalid category. Must be one of: {[cat.value for cat in HelpStepCategory]}")

        return value

    def serialize(self) -> Dict[str, Any]:
        """Serialize help step data for API responses."""
        return {
            'id': self.id,
            'page_name': self.page_name,
            'target': self.target,
            'content': self.content,
            'order': self.order,
            'category': self.category,
            'version': self.version,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'dependencies': [dep.id for dep in self.dependencies]
        }

    @staticmethod
    def get_steps_by_page(
        page_name: str,
        category: Optional[str] = None,
        include_deleted: bool = False
    ) -> List['HelpStep']:
        """
        Retrieve all help steps for a specific page with optional filters.

        Args:
            page_name: Name of the page to get steps for
            category: Optional category filter
            include_deleted: Whether to include deleted steps

        Returns:
            List of help steps for the page
        """
        query = HelpStep.query.filter_by(page_name=page_name)

        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        if category:
            query = query.filter_by(category=category)

        return query.order_by(HelpStep.order).all()

    @staticmethod
    def get_steps_by_category(
        category: str,
        include_deleted: bool = False
    ) -> List['HelpStep']:
        """
        Retrieve all help steps for a specific category.

        Args:
            category: Category to get steps for
            include_deleted: Whether to include deleted steps

        Returns:
            List of help steps for the category
        """
        query = HelpStep.query.filter_by(category=category)

        if not include_deleted:
            query = query.filter_by(is_deleted=False)

        return query.order_by(HelpStep.order).all()

    @staticmethod
    def search_steps(
        query: str,
        category: Optional[str] = None
    ) -> List['HelpStep']:
        """
        Search help steps by content or page name.

        Args:
            query: Search query string
            category: Optional category filter

        Returns:
            List of matching help steps
        """
        filters = [
            HelpStep.is_deleted.is_(False),
            or_(
                HelpStep.content.ilike(f'%{query}%'),
                HelpStep.page_name.ilike(f'%{query}%')
            )
        ]

        if category:
            filters.append(HelpStep.category == category)

        return HelpStep.query.filter(and_(*filters)).order_by(HelpStep.order).all()


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
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_template = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationships
    steps = db.relationship(
        'HelpStep',
        secondary=help_tour_steps,
        backref='help_tours',
        lazy='selectin'
    )
    user = db.relationship('User', backref='help_tours')

    __table_args__ = (
        db.Index('idx_help_tour_template', 'is_template'),
    )

    def serialize(self) -> Dict[str, Any]:
        """Serialize help tour data for API responses."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'is_template': self.is_template,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'steps': [step.serialize() for step in self.steps]
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
        help_tour = HelpTour.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).first()
        logger.info(f"Retrieved help tour status for user_id: {user_id}")
        return help_tour

    @staticmethod
    def get_templates() -> List['HelpTour']:
        """
        Retrieve all help tour templates.

        Returns:
            List of help tour templates
        """
        return HelpTour.query.filter_by(is_template=True, is_deleted=False).all()

    @staticmethod
    def create_from_template(template_id: int, user_id: int) -> Optional['HelpTour']:
        """
        Create a new help tour from a template.

        Args:
            template_id: ID of the template to use
            user_id: ID of the user to create tour for

        Returns:
            New HelpTour object or None if template not found
        """
        template = HelpTour.query.filter_by(
            id=template_id,
            is_template=True,
            is_deleted=False
        ).first()

        if not template:
            return None

        new_tour = HelpTour(
            user_id=user_id,
            name=template.name,
            description=template.description
        )
        new_tour.steps = template.steps.copy()

        db.session.add(new_tour)
        db.session.commit()

        return new_tour

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
            logger.error(f"Error resetting help tour for user_id: {user_id}")
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
