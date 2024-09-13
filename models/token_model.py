from app import db, logger
from datetime import datetime

# TokenBlacklist model for managing blacklisted (revoked) JWT tokens
class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID (unique identifier for the token)
    token_type = db.Column(db.String(10), nullable=False, index=True)  # Token type: access or refresh
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    revoked = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expire_at = db.Column(db.DateTime, nullable=False)

    # Relationship with User
    user = db.relationship('User', backref='blacklisted_tokens')

    def serialize(self):
        """Serialize the token blacklist entry to JSON-friendly format."""
        return {
            'id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_id': self.user_id,
            'revoked': self.revoked,
            'created_at': self.created_at.isoformat()
        }

    def revoke(self):
        """Mark the token as revoked if not already revoked."""
        if not self.revoked:
            try:
                self.revoked = True
                db.session.commit()
                logger.info(f"Token {self.jti} for user {self.user_id} revoked.")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to revoke token {self.jti}: {e}")
                raise ValueError("Token revocation failed.")

    def is_revoked(self):
        """Check if the token is revoked."""
        return self.revoked


# RefreshToken model for managing long-lived refresh tokens
class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)  # Store the refresh token itself
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked = db.Column(db.Boolean, default=False, index=True)  # Add revoked flag
    expire_at = db.Column(db.DateTime, nullable=False)

    # Relationship with User
    user = db.relationship('User', backref='refresh_tokens')

    def serialize(self):
        """Serialize the refresh token entry to JSON-friendly format."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'created_at': self.created_at.isoformat(),
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked': self.revoked
        }

    def revoke(self):
        """Mark the refresh token as revoked if not already revoked."""
        if not self.revoked:
            try:
                self.revoked_at = datetime.utcnow()
                self.revoked = True
                db.session.commit()
                logger.info(f"Refresh token {self.token} for user {self.user_id} revoked.")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to revoke refresh token {self.token}: {e}")
                raise ValueError("Refresh token revocation failed.")

    def is_revoked(self):
        """Check if the refresh token is revoked."""
        return self.revoked
