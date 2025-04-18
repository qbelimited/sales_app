from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import and_, func
from models.retention_model import RetentionPolicy, DataType
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TokenBlacklist model for managing blacklisted (revoked) JWT tokens
class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)  # JWT ID (unique identifier for the token)
    token_type = db.Column(db.String(10), nullable=False, index=True)  # Token type: access or refresh
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    revoked = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expire_at = db.Column(db.DateTime, nullable=False)
    device_info = db.Column(db.String(255), nullable=True)  # Store device information
    ip_address = db.Column(db.String(45), nullable=True)  # Store IP address
    last_used = db.Column(db.DateTime, nullable=True)  # Track last usage
    usage_count = db.Column(db.Integer, default=0)  # Track number of times token was used
    security_level = db.Column(db.String(20), default='standard')  # Track security level
    is_deleted = db.Column(db.Boolean, default=False, index=True)  # Soft delete flag

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
            'created_at': self.created_at.isoformat(),
            'expire_at': self.expire_at.isoformat(),
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'security_level': self.security_level,
            'is_deleted': self.is_deleted
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

    def update_last_used(self):
        """Update the last used timestamp and increment usage count."""
        try:
            self.last_used = datetime.utcnow()
            self.usage_count += 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update token usage: {e}")

    @staticmethod
    def cleanup_expired_tokens():
        """Clean up expired tokens based on retention policy."""
        try:
            # Get retention policy for tokens
            policy = RetentionPolicy.get_policy(DataType.USER_SESSIONS.value)
            cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)

            # Get tokens to delete
            tokens_to_delete = TokenBlacklist.query.filter(
                and_(
                    TokenBlacklist.expire_at < cutoff_date,
                    TokenBlacklist.is_deleted == False
                )
            ).all()

            # Archive tokens if required by policy
            if policy.archive_before_delete:
                for token in tokens_to_delete:
                    # Archive token data
                    archived_data = ArchivedData(
                        data_type=DataType.USER_SESSIONS.value,
                        original_id=token.id,
                        retention_policy_id=policy.id
                    )
                    archived_data.compress_data(token.serialize())
                    db.session.add(archived_data)

            # Mark tokens as deleted
            for token in tokens_to_delete:
                token.is_deleted = True

            db.session.commit()
            return len(tokens_to_delete)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up expired tokens: {e}")
            raise ValueError(f"Error cleaning up expired tokens: {e}")

    @staticmethod
    def get_active_tokens():
        """Get all non-deleted tokens."""
        return TokenBlacklist.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_expired_tokens():
        """Get all expired but not deleted tokens."""
        return TokenBlacklist.query.filter(
            and_(
                TokenBlacklist.expire_at < datetime.utcnow(),
                TokenBlacklist.is_deleted == False
            )
        ).all()

    @staticmethod
    def is_token_valid(jti):
        """Check if a token is valid (not revoked and not expired)."""
        token = TokenBlacklist.query.filter_by(jti=jti).first()
        if not token:
            return True
        return not token.revoked and token.expire_at > datetime.utcnow()

    @staticmethod
    def get_usage_analytics(user_id=None):
        """Get token usage analytics."""
        query = TokenBlacklist.query
        if user_id:
            query = query.filter_by(user_id=user_id)

        return {
            'total_tokens': query.count(),
            'active_tokens': query.filter(
                TokenBlacklist.revoked == False,
                TokenBlacklist.expire_at > datetime.utcnow()
            ).count(),
            'revoked_tokens': query.filter_by(revoked=True).count(),
            'expired_tokens': query.filter(
                TokenBlacklist.expire_at < datetime.utcnow()
            ).count(),
            'average_usage': db.session.query(
                func.avg(TokenBlacklist.usage_count)
            ).scalar() or 0
        }

    @staticmethod
    def check_rate_limit(ip_address, user_id, max_requests=100, time_window=3600):
        """Check if the rate limit has been exceeded."""
        recent_tokens = TokenBlacklist.query.filter(
            TokenBlacklist.ip_address == ip_address,
            TokenBlacklist.user_id == user_id,
            TokenBlacklist.created_at > datetime.utcnow() - timedelta(seconds=time_window)
        ).count()

        return recent_tokens < max_requests


# RefreshToken model for managing long-lived refresh tokens
class RefreshToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.Text, unique=True, nullable=False)  # Store the refresh token itself
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked = db.Column(db.Boolean, default=False, index=True)  # Add revoked flag
    expire_at = db.Column(db.DateTime, nullable=False)
    device_info = db.Column(db.String(255), nullable=True)  # Store device information
    ip_address = db.Column(db.String(45), nullable=True)  # Store IP address
    last_used = db.Column(db.DateTime, nullable=True)  # Track last usage
    token_family = db.Column(db.String(36), nullable=True, index=True)  # Track token family for rotation
    rotation_count = db.Column(db.Integer, default=0)  # Track number of rotations
    usage_count = db.Column(db.Integer, default=0)  # Track number of times token was used
    security_level = db.Column(db.String(20), default='standard')  # Track security level

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
            'revoked': self.revoked,
            'expire_at': self.expire_at.isoformat(),
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'token_family': self.token_family,
            'rotation_count': self.rotation_count,
            'usage_count': self.usage_count,
            'security_level': self.security_level
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
                logger.error(f"Failed to revoke refresh token: {e}")
                raise ValueError("Refresh token revocation failed.")

    def is_revoked(self):
        """Check if the refresh token is revoked."""
        return self.revoked

    def update_last_used(self):
        """Update the last used timestamp and increment usage count."""
        try:
            self.last_used = datetime.utcnow()
            self.usage_count += 1
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update refresh token usage: {e}")

    def rotate(self, new_token):
        """Rotate the refresh token and update rotation count."""
        try:
            self.rotation_count += 1
            self.token = new_token
            db.session.commit()
            logger.info(f"Refresh token rotated for user {self.user_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to rotate refresh token: {e}")
            raise ValueError("Refresh token rotation failed.")

    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired refresh tokens."""
        try:
            expired_tokens = RefreshToken.query.filter(
                RefreshToken.expire_at < datetime.utcnow()
            ).all()

            for token in expired_tokens:
                db.session.delete(token)

            db.session.commit()
            logger.info(f"Cleaned up {len(expired_tokens)} expired refresh tokens")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup expired refresh tokens: {e}")

    @staticmethod
    def revoke_token_family(token_family):
        """Revoke all tokens in a token family."""
        try:
            tokens = RefreshToken.query.filter_by(token_family=token_family).all()
            for token in tokens:
                token.revoke()
            db.session.commit()
            logger.info(f"Revoked all tokens in family {token_family}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to revoke token family: {e}")
            raise ValueError("Token family revocation failed.")

    @staticmethod
    def get_usage_analytics(user_id=None):
        """Get refresh token usage analytics."""
        query = RefreshToken.query
        if user_id:
            query = query.filter_by(user_id=user_id)

        return {
            'total_tokens': query.count(),
            'active_tokens': query.filter(
                RefreshToken.revoked == False,
                RefreshToken.expire_at > datetime.utcnow()
            ).count(),
            'revoked_tokens': query.filter_by(revoked=True).count(),
            'expired_tokens': query.filter(
                RefreshToken.expire_at < datetime.utcnow()
            ).count(),
            'average_rotations': db.session.query(
                func.avg(RefreshToken.rotation_count)
            ).scalar() or 0,
            'average_usage': db.session.query(
                func.avg(RefreshToken.usage_count)
            ).scalar() or 0
        }

    @staticmethod
    def check_rate_limit(ip_address, user_id, max_requests=50, time_window=3600):
        """Check if the rate limit has been exceeded."""
        recent_tokens = RefreshToken.query.filter(
            RefreshToken.ip_address == ip_address,
            RefreshToken.user_id == user_id,
            RefreshToken.created_at > datetime.utcnow() - timedelta(seconds=time_window)
        ).count()

        return recent_tokens < max_requests
