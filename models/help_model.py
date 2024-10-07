from app import db, logger
from datetime import datetime
from sqlalchemy.exc import IntegrityError  # Import specific exceptions

# Association table for many-to-many relationship between HelpTour and HelpStep
help_tour_steps = db.Table('help_tour_steps',
    db.Column('help_tour_id', db.Integer, db.ForeignKey('help_tour.id'), primary_key=True),
    db.Column('help_step_id', db.Integer, db.ForeignKey('help_step.id'), primary_key=True)
)

class HelpStep(db.Model):
    __tablename__ = 'help_step'

    id = db.Column(db.Integer, primary_key=True)
    page_name = db.Column(db.String(100), nullable=False)  # Name of the page
    target = db.Column(db.String(255), nullable=False)      # Target element to highlight
    content = db.Column(db.Text, nullable=False)            # Content of the help step
    order = db.Column(db.Integer, nullable=False)           # Order of the help step

    __table_args__ = (
        db.UniqueConstraint('page_name', 'order', name='uq_page_order'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'page_name': self.page_name,
            'target': self.target,
            'content': self.content,
            'order': self.order,
        }

class HelpTour(db.Model):
    __tablename__ = 'help_tour'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)  # Flag to check if the tour is completed
    completed_at = db.Column(db.DateTime, nullable=True)  # Timestamp of when the tour was completed
    steps = db.relationship('HelpStep', secondary=help_tour_steps, backref='help_tours')

    user = db.relationship('User', backref='help_tours')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'steps': [step.serialize() for step in self.steps]  # Include steps in the serialized output
        }

    @staticmethod
    def get_user_help_tour_status(user_id):
        """Retrieve the help tour status for a specific user."""
        help_tour = HelpTour.query.filter_by(user_id=user_id).first()
        logger.info(f"Retrieved help tour status for user_id: {user_id} - {help_tour}")
        return help_tour

    @staticmethod
    def set_user_help_tour_completed(user_id):
        """Mark the Help Tour as completed for a specific user."""
        help_tour = HelpTour.get_user_help_tour_status(user_id)
        try:
            if help_tour:
                help_tour.completed = True
                help_tour.completed_at = datetime.utcnow()
                logger.info(f"Marked existing help tour as completed for user_id: {user_id}")
            else:
                help_tour = HelpTour(user_id=user_id, completed=True, completed_at=datetime.utcnow())
                db.session.add(help_tour)
                logger.info(f"Created new help tour for user_id: {user_id}")

            db.session.commit()
            logger.info(f"Successfully committed help tour status for user_id: {user_id}")
        except IntegrityError as ie:
            db.session.rollback()  # Rollback the session in case of integrity error
            logger.error(f"Integrity error while setting help tour completed for user_id: {user_id} - {ie}")
            raise
        except Exception as e:
            db.session.rollback()  # Rollback the session in case of any other error
            logger.error(f"Error while setting help tour completed for user_id: {user_id} - {e}")
            raise

    @staticmethod
    def get_steps_for_page(page_name):
        """Retrieve all help steps for a specific page."""
        steps = HelpStep.query.filter_by(page_name=page_name).order_by(HelpStep.order).all()
        logger.info(f"Retrieved {len(steps)} help steps for page: {page_name}")
        return steps
