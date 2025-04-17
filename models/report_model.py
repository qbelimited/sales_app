from app import db, logger
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
from enum import Enum
from sqlalchemy import JSON, and_, or_


class ReportType(Enum):
    """Predefined report types in the system."""
    SALES_PERFORMANCE = 'sales_performance'
    PAYPOINT_PERFORMANCE = 'paypoint_performance'
    PRODUCT_PERFORMANCE = 'product_performance'
    FRAUD_DETECTION = 'fraud_detection'
    INCEPTION = 'inception'
    TEAM_PERFORMANCE = 'team_performance'
    CUSTOM = 'custom'


class ReportSchedule(Enum):
    """Report scheduling options."""
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    YEARLY = 'yearly'
    MANUAL = 'manual'


class ReportAccessLevel(Enum):
    """Report access levels."""
    PUBLIC = 'public'
    PRIVATE = 'private'
    ROLE_BASED = 'role_based'


class Report(db.Model):
    """Model representing a user-generated report."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False,
        index=True
    )
    report_type = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    parameters = db.Column(JSON, nullable=True)  # Store report parameters as JSON
    schedule = db.Column(
        db.String(20),
        nullable=False,
        default=ReportSchedule.MANUAL.value
    )
    access_level = db.Column(
        db.String(20),
        nullable=False,
        default=ReportAccessLevel.PRIVATE.value
    )
    allowed_roles = db.Column(JSON, nullable=True)  # List of role IDs with access
    last_run_at = db.Column(db.DateTime, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    is_active = db.Column(db.Boolean, default=True, index=True)

    # Relationship to the User
    user = db.relationship('User', backref='reports')

    @validates('report_type')
    def validate_report_type(self, _, rt):
        """Validate that the report type is valid."""
        if not rt or rt.strip() == "":
            raise ValueError("Report type cannot be empty")
        try:
            ReportType(rt)
        except ValueError:
            raise ValueError(
                f"Invalid report type: {rt}"
            )
        return rt

    @validates('schedule')
    def validate_schedule(self, _, sched):
        """Validate that the schedule is valid."""
        try:
            ReportSchedule(sched)
        except ValueError:
            raise ValueError(f"Invalid schedule: {sched}")
        return sched

    @validates('access_level')
    def validate_access_level(self, _, al):
        """Validate that the access level is valid."""
        try:
            ReportAccessLevel(al)
        except ValueError:
            raise ValueError(
                f"Invalid access level: {al}"
            )
        return al

    def has_access(self, user_id, user_role_id=None):
        """Check if a user has access to this report."""
        if self.access_level == ReportAccessLevel.PUBLIC.value:
            return True

        if self.access_level == ReportAccessLevel.PRIVATE.value:
            return self.user_id == user_id

        if self.access_level == ReportAccessLevel.ROLE_BASED.value:
            if self.allowed_roles and user_role_id:
                return user_role_id in self.allowed_roles

        return False

    def serialize(self):
        """Serialize the report object."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_type': self.report_type,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'schedule': self.schedule,
            'access_level': self.access_level,
            'allowed_roles': self.allowed_roles,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted,
            'is_active': self.is_active
        }

    def calculate_next_run(self):
        """Calculate the next run time based on the schedule."""
        if self.schedule == ReportSchedule.MANUAL.value:
            return None

        now = datetime.utcnow()
        if self.schedule == ReportSchedule.DAILY.value:
            return now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=1)
        elif self.schedule == ReportSchedule.WEEKLY.value:
            return now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=7)
        elif self.schedule == ReportSchedule.MONTHLY.value:
            return (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        elif self.schedule == ReportSchedule.QUARTERLY.value:
            quarter = (now.month - 1) // 3
            next_quarter = (quarter + 1) % 4
            next_year = now.year + (quarter == 3)
            return datetime(next_year, next_quarter * 3 + 1, 1)
        elif self.schedule == ReportSchedule.YEARLY.value:
            return now.replace(year=now.year + 1, month=1, day=1)
        return None

    def update_schedule(self):
        """Update the report's schedule and next run time."""
        if self.schedule != ReportSchedule.MANUAL.value:
            self.next_run_at = self.calculate_next_run()
            self.last_run_at = datetime.utcnow()
            db.session.commit()

    @staticmethod
    def get_active_reports(page=1, per_page=10, sort_by="created_at", sort_order="desc"):
        """Retrieve a paginated list of active reports with sorting and pagination."""
        try:
            query = Report.query.filter_by(is_deleted=False, is_active=True)
            order = getattr(Report, sort_by).desc() if sort_order == "desc" else getattr(Report, sort_by).asc()
            return query.order_by(order).paginate(page=page, per_page=per_page)
        except AttributeError:
            raise ValueError(f"Invalid sort field: {sort_by}")
        except Exception as e:
            logger.error(f"Error fetching active reports: {e}")
            raise ValueError(f"Error fetching active reports: {e}")

    @staticmethod
    def get_scheduled_reports():
        """Get all reports that are due to run."""
        now = datetime.utcnow()
        return Report.query.filter(
            Report.is_deleted is False,
            Report.is_active is True,
            Report.schedule != ReportSchedule.MANUAL.value,
            Report.next_run_at <= now
        ).all()

    @staticmethod
    def get_reports_by_type(report_type, page=1, per_page=10, sort_by="created_at", sort_order="desc"):
        """Retrieve a paginated list of reports by type with sorting and pagination."""
        try:
            query = Report.query.filter_by(report_type=report_type, is_deleted=False)
            order = getattr(Report, sort_by).desc() if sort_order == "desc" else getattr(Report, sort_by).asc()
            return query.order_by(order).paginate(page=page, per_page=per_page)
        except AttributeError:
            raise ValueError(f"Invalid sort field: {sort_by}")
        except Exception as e:
            logger.error(f"Error fetching reports by type: {e}")
            raise ValueError(f"Error fetching reports by type: {e}")

    @staticmethod
    def get_user_reports(
        user_id,
        user_role_id=None,
        page=1,
        per_page=10,
        sort_by="created_at",
        sort_order="desc"
    ):
        """Get reports accessible to a specific user."""
        try:
            query = Report.query.filter(
                Report.is_deleted is False,
                Report.is_active is True,
                or_(
                    Report.access_level == ReportAccessLevel.PUBLIC.value,
                    Report.user_id == user_id,
                    and_(
                        Report.access_level == ReportAccessLevel.ROLE_BASED.value,
                        Report.allowed_roles.contains([user_role_id])
                    )
                )
            )
            order = getattr(Report, sort_by).desc() if sort_order == "desc" else getattr(Report, sort_by).asc()
            return query.order_by(order).paginate(page=page, per_page=per_page)
        except Exception as e:
            logger.error(f"Error fetching user reports: {e}")
            raise ValueError(f"Error fetching user reports: {e}")

    @staticmethod
    def filter_reports(
        filters,
        user_id=None,
        user_role_id=None,
        page=1,
        per_page=10,
        sort_by="created_at",
        sort_order="desc"
    ):
        """Filter reports with access control."""
        try:
            query = Report.query.filter(Report.is_deleted is False)

            # Apply access control if user context is provided
            if user_id is not None:
                query = query.filter(
                    or_(
                        Report.access_level == ReportAccessLevel.PUBLIC.value,
                        Report.user_id == user_id,
                        and_(
                            Report.access_level == ReportAccessLevel.ROLE_BASED.value,
                            Report.allowed_roles.contains([user_role_id])
                        )
                    )
                )

            # Apply additional filters
            for key, value in filters.items():
                if hasattr(Report, key) and value is not None:
                    query = query.filter(getattr(Report, key) == value)

            order = getattr(Report, sort_by).desc() if sort_order == "desc" else getattr(Report, sort_by).asc()
            return query.order_by(order).paginate(page=page, per_page=per_page)
        except Exception as e:
            logger.error(f"Error filtering reports: {e}")
            raise ValueError(f"Error filtering reports: {e}")

    @staticmethod
    def soft_delete(report_id):
        """Soft delete a report by marking it as deleted."""
        try:
            report = Report.query.filter_by(id=report_id).first()
            if not report or report.is_deleted:
                raise ValueError(f"Report with ID {report_id} not found or already deleted")
            report.is_deleted = True
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error soft deleting report: {e}")
            raise ValueError(f"Error soft deleting report: {e}")

    @staticmethod
    def restore_deleted(report_id):
        """Restore a soft-deleted report."""
        try:
            report = Report.query.filter_by(id=report_id).first()
            if not report or not report.is_deleted:
                raise ValueError(f"Report with ID {report_id} not found or not deleted")
            report.is_deleted = False
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error restoring report: {e}")
            raise ValueError(f"Error restoring report: {e}")


class CustomReport(db.Model):
    """Model representing a user-defined custom report."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fields = db.Column(db.JSON, nullable=False)  # Store fields as a JSON array
    group_by = db.Column(db.String(100), nullable=True)  # Group by field
    aggregations = db.Column(db.JSON, nullable=True)  # Store aggregations as a JSON
    filters = db.Column(db.JSON, nullable=True)  # Store filters as a JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete field

    def serialize(self):
        """Serialize the custom report object."""
        return {
            'id': self.id,
            'name': self.name,
            'fields': self.fields,
            'group_by': self.group_by,
            'aggregations': self.aggregations,
            'filters': self.filters,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted
        }

    @staticmethod
    def soft_delete(custom_report_id):
        """Soft delete a custom report by marking it as deleted."""
        try:
            custom_report = CustomReport.query.filter_by(id=custom_report_id).first()
            if not custom_report or custom_report.is_deleted:
                raise ValueError(f"CustomReport with ID {custom_report_id} not found or already deleted")
            custom_report.is_deleted = True
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error soft deleting custom report: {e}")
            raise ValueError(f"Error soft deleting custom report: {e}")

    @staticmethod
    def restore_deleted(custom_report_id):
        """Restore a soft-deleted custom report."""
        try:
            custom_report = CustomReport.query.filter_by(id=custom_report_id).first()
            if not custom_report or not custom_report.is_deleted:
                raise ValueError(f"CustomReport with ID {custom_report_id} not found or not deleted")
            custom_report.is_deleted = False
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error restoring custom report: {e}")
            raise ValueError(f"Error restoring custom report: {e}")
