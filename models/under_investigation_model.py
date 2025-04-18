from extensions import db
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
from enum import Enum
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class InvestigationPriority(Enum):
    """Priority levels for investigations."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class InvestigationStatus(Enum):
    """Status of an investigation."""
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    PENDING_REVIEW = 'pending_review'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


class InvestigationCategory(Enum):
    """Categories of investigations."""
    FRAUD = 'fraud'
    COMPLIANCE = 'compliance'
    CUSTOMER_SERVICE = 'customer_service'
    DATA_QUALITY = 'data_quality'
    OPERATIONAL = 'operational'
    OTHER = 'other'


class InvestigationSLA(db.Model):
    """Service Level Agreement for investigations."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    priority = db.Column(db.String(20), nullable=False, index=True)
    target_resolution_days = db.Column(db.Integer, nullable=False)
    warning_threshold_days = db.Column(db.Integer, nullable=False)
    breach_threshold_days = db.Column(db.Integer, nullable=False)
    escalation_path = db.Column(db.Text, nullable=True)  # JSON string of escalation steps
    notification_settings = db.Column(db.Text, nullable=True)  # JSON string of notification rules
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    @validates('target_resolution_days', 'warning_threshold_days', 'breach_threshold_days')
    def validate_days(self, key, value):
        """Validate SLA time thresholds."""
        if value <= 0:
            raise ValueError(f"{key} must be positive")
        if key == 'warning_threshold_days' and (
            value >= self.breach_threshold_days
        ):
            raise ValueError(
                "Warning threshold must be less than breach threshold"
            )
        if key == 'target_resolution_days' and value >= self.warning_threshold_days:
            raise ValueError("Target resolution must be less than warning threshold")
        return value

    def calculate_due_dates(self, start_date):
        """Calculate warning and breach dates."""
        return {
            'target_date': start_date + timedelta(days=self.target_resolution_days),
            'warning_date': start_date + timedelta(days=self.warning_threshold_days),
            'breach_date': start_date + timedelta(days=self.breach_threshold_days)
        }

    def get_escalation_path(self):
        """Get escalation steps as a list."""
        return json.loads(self.escalation_path) if self.escalation_path else []

    def get_notification_settings(self):
        """Get notification rules as a dict."""
        return json.loads(self.notification_settings) if self.notification_settings else {}

    def serialize(self):
        """Serialize SLA data."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'target_resolution_days': self.target_resolution_days,
            'warning_threshold_days': self.warning_threshold_days,
            'breach_threshold_days': self.breach_threshold_days,
            'escalation_path': self.get_escalation_path(),
            'notification_settings': self.get_notification_settings(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_sla_for_investigation(category, priority):
        """Get appropriate SLA for investigation parameters."""
        return InvestigationSLA.query.filter_by(
            category=category,
            priority=priority,
            is_active=True
        ).first()


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
    priority = db.Column(db.String(20), default=InvestigationPriority.MEDIUM.value, index=True)
    status = db.Column(db.String(20), default=InvestigationStatus.OPEN.value, index=True)
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    estimated_resolution_date = db.Column(db.DateTime, nullable=True)
    last_status_change = db.Column(db.DateTime, default=datetime.utcnow)
    status_history = db.Column(db.Text, nullable=True)  # JSON string of status changes
    risk_score = db.Column(db.Float, nullable=True)  # Calculated risk score
    tags = db.Column(db.String(255), nullable=True)  # Comma-separated tags for categorization
    category = db.Column(db.String(50), default=InvestigationCategory.OTHER.value, index=True)
    sla_id = db.Column(db.Integer, db.ForeignKey('investigation_sla.id'), nullable=True)
    sla_status = db.Column(db.String(20), default='on_track', index=True)  # on_track, warning, breached
    sla_warning_date = db.Column(db.DateTime, nullable=True)
    sla_breach_date = db.Column(db.DateTime, nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('investigation_template.id'), nullable=True)
    custom_fields = db.Column(db.Text, nullable=True)  # JSON string for additional fields
    attachments = db.Column(db.Text, nullable=True)  # JSON string of attachment references
    related_investigations = db.Column(db.Text, nullable=True)  # JSON string of related investigation IDs

    # Relationships
    sale = db.relationship('Sale', backref='under_investigations')
    updated_by = db.relationship('User', foreign_keys=[updated_by_user_id], backref='investigation_updates')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_user_id], backref='assigned_investigations')
    template = db.relationship('InvestigationTemplate', backref='investigations')
    sla = db.relationship('InvestigationSLA', backref='investigations')

    @validates('reason')
    def validate_reason(self, _, reason):
        if not reason or len(reason.strip()) < 5:
            raise ValueError("Reason must be at least 5 characters long")
        return reason.strip()

    @validates('resolved_at')
    def validate_resolved_at(self, _, resolved_at):
        if self.resolved and not resolved_at:
            raise ValueError("Resolved date must be provided when marking investigation as resolved")
        if resolved_at and resolved_at < self.flagged_at:
            raise ValueError("Resolved date cannot be before flagged date")
        return resolved_at

    @validates('priority')
    def validate_priority(self, _, priority):
        try:
            InvestigationPriority(priority)
            return priority
        except ValueError:
            raise ValueError(f"Invalid priority. Must be one of: {[p.value for p in InvestigationPriority]}")

    @validates('status')
    def validate_status(self, _, status):
        try:
            InvestigationStatus(status)
            return status
        except ValueError:
            raise ValueError(f"Invalid status. Must be one of: {[s.value for s in InvestigationStatus]}")

    @validates('category')
    def validate_category(self, _, category):
        try:
            InvestigationCategory(category)
            return category
        except ValueError:
            raise ValueError(f"Invalid category. Must be one of: {[c.value for c in InvestigationCategory]}")

    def add_note_with_history(self, new_note, user_id):
        """Updates the notes, keeps track of note history, and logs who updated it."""
        try:
            if self.notes:
                # Append old note to the history with a timestamp
                timestamp = datetime.utcnow().isoformat()
                if self.notes_history:
                    self.notes_history += f"\n[{timestamp}] {self.notes}"
                else:
                    self.notes_history = f"[{timestamp}] {self.notes}"
            # Update the note and the user who updated it
            self.notes = new_note
            self.updated_by_user_id = user_id
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error updating notes: {e}")

    def update_status(self, new_status, user_id, notes=None):
        """Update investigation status and maintain history."""
        try:
            old_status = self.status
            self.status = new_status
            self.last_status_change = datetime.utcnow()
            self.updated_by_user_id = user_id

            # Update status history
            status_change = {
                'timestamp': datetime.utcnow().isoformat(),
                'old_status': old_status,
                'new_status': new_status,
                'user_id': user_id,
                'notes': notes
            }

            if self.status_history:
                history = json.loads(self.status_history)
                history.append(status_change)
                self.status_history = json.dumps(history)
            else:
                self.status_history = json.dumps([status_change])

            if notes:
                self.add_note_with_history(notes, user_id)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error updating status: {e}")

    def assign_to(self, user_id, notes=None):
        """Assign investigation to a user."""
        try:
            self.assigned_to_user_id = user_id
            if notes:
                self.add_note_with_history(notes, user_id)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error assigning investigation: {e}")

    def calculate_risk_score(self):
        """Calculate risk score based on various factors."""
        try:
            risk_score = 0.0

            # Base risk from priority
            priority_risk = {
                InvestigationPriority.LOW.value: 0.2,
                InvestigationPriority.MEDIUM.value: 0.5,
                InvestigationPriority.HIGH.value: 0.8,
                InvestigationPriority.CRITICAL.value: 1.0
            }
            risk_score += priority_risk[self.priority]

            # Risk from duration
            days_open = (datetime.utcnow() - self.flagged_at).days
            if days_open > 7:
                risk_score += min(0.3, days_open / 30)

            # Risk from status
            if self.status == InvestigationStatus.IN_PROGRESS.value:
                risk_score += 0.1
            elif self.status == InvestigationStatus.PENDING_REVIEW.value:
                risk_score += 0.2

            # Risk from SLA breach
            if self.sla_status == 'breached':
                risk_score += 0.2

            self.risk_score = min(1.0, risk_score)
            db.session.commit()
            return self.risk_score
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return None

    def update_sla_status(self):
        """Update SLA status based on current date and thresholds."""
        if not self.sla or self.resolved:
            return

        now = datetime.utcnow()
        if now > self.sla_breach_date:
            self.sla_status = 'breached'
        elif now > self.sla_warning_date:
            self.sla_status = 'warning'
        else:
            self.sla_status = 'on_track'

        db.session.commit()

    def set_sla(self, sla_id=None):
        """Set or update SLA for the investigation."""
        if sla_id:
            self.sla_id = sla_id
        else:
            sla = InvestigationSLA.get_sla_for_investigation(self.category, self.priority)
            if sla:
                self.sla_id = sla.id
                dates = sla.calculate_due_dates(self.flagged_at)
                self.sla_warning_date = dates['warning_date']
                self.sla_breach_date = dates['breach_date']
                self.update_sla_status()
        db.session.commit()

    def get_sla_metrics(self):
        """Get SLA-related metrics."""
        if not self.sla or not self.resolved:
            return None

        resolution_time = (self.resolved_at - self.flagged_at).days
        return {
            'target_days': self.sla.target_resolution_days,
            'actual_days': resolution_time,
            'status': self.sla_status,
            'breached': resolution_time > self.sla.breach_threshold_days,
            'warning': resolution_time > self.sla.warning_threshold_days
        }

    def add_attachment(self, attachment_id, description):
        """Add an attachment reference to the investigation."""
        try:
            attachments = json.loads(self.attachments) if self.attachments else []
            attachments.append({
                'id': attachment_id,
                'description': description,
                'added_at': datetime.utcnow().isoformat()
            })
            self.attachments = json.dumps(attachments)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error adding attachment: {e}")

    def add_related_investigation(self, related_id, relationship_type):
        """Add a related investigation reference."""
        try:
            related = json.loads(self.related_investigations) if self.related_investigations else []
            related.append({
                'id': related_id,
                'type': relationship_type,
                'added_at': datetime.utcnow().isoformat()
            })
            self.related_investigations = json.dumps(related)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error adding related investigation: {e}")

    def resolve_investigation(self, resolved_by_user_id, resolution_notes=None):
        """Marks the investigation as resolved and records the resolution time."""
        if self.resolved:
            raise ValueError("Investigation is already resolved")
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.updated_by_user_id = resolved_by_user_id
        if resolution_notes:
            self.add_note_with_history(resolution_notes, resolved_by_user_id)
        self.update_status(InvestigationStatus.RESOLVED.value, resolved_by_user_id, resolution_notes)
        db.session.commit()

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
            'updated_by_user_id': self.updated_by_user_id,
            'priority': self.priority,
            'status': self.status,
            'assigned_to_user_id': self.assigned_to_user_id,
            'estimated_resolution_date': self.estimated_resolution_date.isoformat() if self.estimated_resolution_date else None,
            'last_status_change': self.last_status_change.isoformat(),
            'status_history': json.loads(self.status_history) if self.status_history else [],
            'risk_score': self.risk_score,
            'tags': self.tags.split(',') if self.tags else [],
            'category': self.category,
            'sla_status': self.sla_status,
            'sla_warning_date': self.sla_warning_date.isoformat() if self.sla_warning_date else None,
            'sla_breach_date': self.sla_breach_date.isoformat() if self.sla_breach_date else None,
            'template_id': self.template_id,
            'custom_fields': json.loads(self.custom_fields) if self.custom_fields else {},
            'attachments': json.loads(self.attachments) if self.attachments else [],
            'related_investigations': json.loads(self.related_investigations) if self.related_investigations else []
        }

    @staticmethod
    def get_active_investigations(page=1, per_page=10, priority=None, status=None, category=None):
        """Retrieve paginated list of active investigations with optional filters."""
        try:
            query = UnderInvestigation.query.filter_by(resolved=False)
            if priority:
                query = query.filter_by(priority=priority)
            if status:
                query = query.filter_by(status=status)
            if category:
                query = query.filter_by(category=category)
            return query.paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching active investigations: {e}")

    @staticmethod
    def get_resolved_investigations(page=1, per_page=10):
        """Retrieve paginated list of resolved investigations."""
        try:
            return UnderInvestigation.query.filter_by(resolved=True).paginate(page=page, per_page=per_page).items
        except Exception as e:
            raise ValueError(f"Error fetching resolved investigations: {e}")

    @staticmethod
    def get_investigation_analytics():
        """Get analytics about investigations."""
        try:
            total = UnderInvestigation.query.count()
            active = UnderInvestigation.query.filter_by(resolved=False).count()
            resolved = UnderInvestigation.query.filter_by(resolved=True).count()

            priority_counts = db.session.query(
                UnderInvestigation.priority,
                db.func.count(UnderInvestigation.id)
            ).group_by(UnderInvestigation.priority).all()

            status_counts = db.session.query(
                UnderInvestigation.status,
                db.func.count(UnderInvestigation.id)
            ).group_by(UnderInvestigation.status).all()

            category_counts = db.session.query(
                UnderInvestigation.category,
                db.func.count(UnderInvestigation.id)
            ).group_by(UnderInvestigation.category).all()

            avg_resolution_time = db.session.query(
                db.func.avg(
                    db.func.extract(
                        'epoch',
                        UnderInvestigation.resolved_at - UnderInvestigation.flagged_at
                    )
                )
            ).filter(UnderInvestigation.resolved).scalar() or 0

            sla_breach_count = UnderInvestigation.query.filter_by(
                sla_status='breached',
                resolved=False
            ).count()

            return {
                'total': total,
                'active': active,
                'resolved': resolved,
                'priority_counts': dict(priority_counts),
                'status_counts': dict(status_counts),
                'category_counts': dict(category_counts),
                'average_resolution_time_seconds': avg_resolution_time,
                'sla_breach_count': sla_breach_count
            }
        except Exception as e:
            logger.error(f"Error getting investigation analytics: {e}")
            return None

class InvestigationTemplate(db.Model):
    """Template for common investigation types."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    default_sla_days = db.Column(db.Integer, nullable=False)
    required_fields = db.Column(db.Text, nullable=True)  # JSON string of required fields
    custom_fields = db.Column(db.Text, nullable=True)  # JSON string of custom field definitions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def create_investigation(self, sale_id, reason, user_id, **kwargs):
        """Create a new investigation based on this template."""
        try:
            investigation = UnderInvestigation(
                sale_id=sale_id,
                reason=reason,
                category=self.category,
                priority=self.priority,
                template_id=self.id,
                updated_by_user_id=user_id
            )

            # Set SLA based on template
            if self.default_sla_days:
                investigation.sla_id = self.id
                dates = self.calculate_due_dates(datetime.utcnow())
                investigation.sla_warning_date = dates['warning_date']
                investigation.sla_breach_date = dates['breach_date']

            # Set custom fields if provided
            if kwargs:
                investigation.custom_fields = json.dumps(kwargs)

            db.session.add(investigation)
            db.session.commit()
            return investigation
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Error creating investigation from template: {e}")

    def calculate_due_dates(self, start_date):
        """Calculate warning and breach dates."""
        return {
            'target_date': start_date + timedelta(days=self.default_sla_days),
            'warning_date': start_date + timedelta(days=self.warning_threshold_days),
            'breach_date': start_date + timedelta(days=self.breach_threshold_days)
        }

    def serialize(self):
        """Serialize template data."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'default_sla_days': self.default_sla_days,
            'required_fields': json.loads(self.required_fields) if self.required_fields else [],
            'custom_fields': json.loads(self.custom_fields) if self.custom_fields else {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
