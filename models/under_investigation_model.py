from app import db
from datetime import datetime

class UnderInvestigation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=False)  # Reason why the sale is under investigation
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the sale was flagged
    resolved = db.Column(db.Boolean, default=False)  # Whether the investigation has been resolved
    resolved_at = db.Column(db.DateTime, nullable=True)  # When the investigation was resolved, if applicable
    notes = db.Column(db.Text, nullable=True)  # Current notes or comments about the investigation
    notes_history = db.Column(db.Text, nullable=True)  # History of old notes
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User who last updated the record

    sale = db.relationship('Sale', backref='under_investigations')
    updated_by = db.relationship('User', backref='investigation_updates')

    def add_note_with_history(self, new_note, user_id):
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

    def serialize(self):
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
