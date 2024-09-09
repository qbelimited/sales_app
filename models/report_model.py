from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    report_type = db.Column(db.String(100), nullable=False, index=True)  # String used for optimization
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    # Relationship to the User
    user = db.relationship('User', backref='reports')

    @validates('report_type')
    def validate_report_type(self, key, report_type):
        if not report_type:
            raise ValueError("Report type cannot be empty")
        return report_type

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_type': self.report_type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_deleted': self.is_deleted
        }

    @staticmethod
    def get_active_reports(page=1, per_page=10):
        """Retrieve paginated list of active reports."""
        try:
            return Report.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active reports: {e}")

    @staticmethod
    def get_reports_by_type(report_type, page=1, per_page=10):
        """Retrieve paginated list of reports by type."""
        try:
            return Report.query.filter_by(report_type=report_type, is_deleted=False).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching reports by type: {e}")
