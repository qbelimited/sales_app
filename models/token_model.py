from app import db
from datetime import datetime

# TokenBlacklist model for managing blacklisted (revoked) JWT tokens
class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID (unique identifier for the token)
    token_type = db.Column(db.String(10), nullable=False, index=True)  # Token type: access or refresh
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    revoked = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with User
    user = db.relationship('User', backref='blacklisted_tokens')

    def serialize(self):
        return {
            'id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_id': self.user_id,
            'revoked': self.revoked,
            'created_at': self.created_at.isoformat()
        }

    def revoke(self):
        """Mark the token as revoked."""
        self.revoked = True
        db.session.commit()

# RefreshToken model for managing long-lived refresh tokens
class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)  # Store the refresh token itself
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked = db.Column(db.Boolean, default=False, index=True)  # Add revoked flag

    # Relationship with User
    user = db.relationship('User', backref='refresh_tokens')

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'created_at': self.created_at.isoformat(),
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked': self.revoked
        }

    def revoke(self):
        """Mark the token as revoked."""
        self.revoked_at = datetime.utcnow()
        self.revoked = True
        db.session.commit()

    def is_revoked(self):
        """Check if the token is revoked."""
        return self.revoked_at is not None