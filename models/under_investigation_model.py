from app import db
from datetime import datetime
from sqlalchemy.orm import validates

class UnderInvestigation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=False)  # Reason why the sale is under investigation
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # When the sale was flagged
    resolved = db.Column(db.Boolean, default=False)  # Whether the investigation has been resolved
    resolved_at = db.Column(db.DateTime, nullable=True, index=True)  # When the investigation was resolved, if applicable
    notes = db.Column(db.Text, nullable=True)  # Current notes or comments about the investigation
    notes_history = db.Column(db.Text, nullable=True)  # History of old notes
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User who last updated the record

    # Relationships
    sale = db.relationship('Sale', backref='under_investigations')
    updated_by = db.relationship('User', backref='investigation_updates')

    @validates('reason')
    def validate_reason(self, _, reason):
        if not reason:
            raise ValueError("Reason cannot be empty")
        return reason

    def add_note_with_history(self, new_note, user_id):
        """Updates the notes, keeps track of note history, and logs who updated it."""
        try:
            if self.notes:
                # Append old note to the history
                if self.notes_history:
                    self.notes_history += f"\n[{datetime.utcnow().isoformat()}] {self.notes}"
                else:
                    self.notes_history = f"[{datetime.utcnow().isoformat()}] {self.notes}"
            # Update the note and the user who updated it
            self.notes = new_note
            self.updated_by_user_id = user_id
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error updating notes: {e}")

    def serialize(self):
        """Serializes the data for use in API responses or frontend display."""
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'reason': self.reason,
            'flagged_at': self.flagged_at.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notes': self.notes,
            'notes_history': self.notes_history,
            'updated_by_user_id': self.updated_by_user_id
        }

    @staticmethod
    def get_active_investigations(page=1, per_page=10):
        """Retrieve paginated list of active investigations."""
        return UnderInvestigation.query.filter_by(resolved=False).paginate(page=page, per_page=per_page).items

    @staticmethod
    def get_resolved_investigations(page=1, per_page=10):
        """Retrieve paginated list of resolved investigations."""
        return UnderInvestigation.query.filter_by(resolved=True).paginate(page=page, per_page=per_page).items
