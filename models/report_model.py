from app import db, logger
from datetime import datetime
from sqlalchemy.orm import validates

class Report(db.Model):
    """Model representing a user-generated report."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    report_type = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete field

    # Relationship to the User
    user = db.relationship('User', backref='reports')

    @validates('report_type')
    def validate_report_type(self, _, report_type):
        if not report_type or report_type.strip() == "":
            raise ValueError("Report type cannot be empty")
        return report_type

    def serialize(self):
        """Serialize the report object."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_type': self.report_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted
        }

    @staticmethod
    def get_active_reports(page=1, per_page=10, sort_by="created_at", sort_order="desc"):
        """Retrieve a paginated list of active reports with sorting and pagination."""
        try:
            query = Report.query.filter_by(is_deleted=False)
            order = getattr(Report, sort_by).desc() if sort_order == "desc" else getattr(Report, sort_by).asc()
            return query.order_by(order).paginate(page=page, per_page=per_page)
        except AttributeError:
            raise ValueError(f"Invalid sort field: {sort_by}")
        except Exception as e:
            logger.error(f"Error fetching active reports: {e}")
            raise ValueError(f"Error fetching active reports: {e}")

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
    def filter_reports(filters, page=1, per_page=10, sort_by="created_at", sort_order="desc"):
        """Filter reports dynamically based on provided filters."""
        try:
            query = Report.query.filter_by(is_deleted=False)
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
