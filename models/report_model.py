from app import db
from datetime import datetime


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    report_type = db.Column(db.String(100), nullable=False, index=True)  # Used String for optimization
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, index=True)

    # Relationship to the User
    user = db.relationship('User', backref='reports')

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
    def get_active_reports():
        """Static method to get non-deleted reports."""
        return Report.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_reports_by_type(report_type):
        """Static method to get reports by type."""
        return Report.query.filter_by(report_type=report_type, is_deleted=False).all()
