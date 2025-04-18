import os
import itertools
from flask_restx import Namespace, Resource, fields
from config import Config
from flask import request
from models.audit_model import AuditTrail, AuditAction
from extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from utils import get_client_ip
from functools import lru_cache
from sqlalchemy import desc, and_, or_

# Define a namespace for log-related operations
log_ns = Namespace('log', description='Log access operations')

# Define models for Swagger documentation
log_model = log_ns.model('Log', {
    'id': fields.Integer(description='Log ID'),
    'timestamp': fields.DateTime(description='Log timestamp'),
    'level': fields.String(description='Log level (INFO, WARNING, ERROR)'),
    'message': fields.String(description='Log message'),
    'user_id': fields.Integer(description='User ID who triggered the log'),
    'resource_type': fields.String(description='Resource type affected'),
    'resource_id': fields.Integer(description='Resource ID affected'),
    'ip_address': fields.String(description='IP address of the user'),
    'user_agent': fields.String(description='User agent of the user')
})

# Define parameters for Swagger documentation
log_param = log_ns.parser()
log_param.add_argument('type', type=str, required=False, default='general',
                      help="Type of log: 'general', 'error', 'success'")
log_param.add_argument('level', type=str, required=False, default='INFO',
                      help="Log level: 'INFO', 'WARNING', 'ERROR'")
log_param.add_argument('page', type=int, required=False, default=1,
                      help="Page number for pagination")
log_param.add_argument('per_page', type=int, required=False, default=50,
                      help="Number of log entries per page")
log_param.add_argument('start_date', type=str, required=False,
                      help="Start date for log filter (YYYY-MM-DD)")
log_param.add_argument('end_date', type=str, required=False,
                      help="End date for log filter (YYYY-MM-DD)")
log_param.add_argument('sort_order', type=str, required=False, default='desc',
                      help="Sort order: 'asc' or 'desc'")
log_param.add_argument('user_id', type=int, required=False,
                      help="Filter by user ID")
log_param.add_argument('resource_type', type=str, required=False,
                      help="Filter by resource type")
log_param.add_argument('action', type=str, required=False,
                      help="Filter by action type")
log_param.add_argument('include_archived', type=str, required=False, default='false',
                      help="Include archived logs")

# Helper function to check role permissions
def check_role_permission(current_user):
    return current_user['role'].lower() in ['admin', 'manager']

@log_ns.route('/')
class LogResource(Resource):
    @log_ns.doc(security='Bearer Auth')
    @log_ns.expect(log_param)
    @jwt_required()
    def get(self):
        """Retrieve logs based on various filters (admin and manager only)."""
        current_user = get_jwt_identity()

        # Check if the user has required permissions
        if not check_role_permission(current_user):
            logger.warning(f"Unauthorized log access attempt by User ID {current_user['id']}")
            return {'message': 'Unauthorized access'}, 403

        # Get query parameters
        log_type = request.args.get('type', 'general').lower()
        level = request.args.get('level', 'INFO').upper()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_order = request.args.get('sort_order', 'desc').lower()
        user_id = request.args.get('user_id', type=int)
        resource_type = request.args.get('resource_type')
        action = request.args.get('action')
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'

        try:
            # Get logs from both file system and database
            file_logs = self.get_file_logs(log_type, level, start_date, end_date)
            db_logs = self.get_db_logs(
                level, start_date, end_date, user_id,
                resource_type, action, include_archived
            )

            # Combine and sort logs
            all_logs = sorted(
                file_logs + db_logs,
                key=lambda x: x.get('timestamp', ''),
                reverse=(sort_order == 'desc')
            )

            # Paginate the logs
            total_logs = len(all_logs)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_logs = all_logs[start_idx:end_idx]

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='log',
                details=f"Accessed {log_type} logs with level {level}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            total_pages = (total_logs + per_page - 1) // per_page

            return {
                'logs': paginated_logs,
                'total_logs': total_logs,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': per_page
            }, 200

        except Exception as e:
            logger.error(f"Error retrieving logs: {str(e)}")
            return {'message': str(e)}, 500

    @lru_cache(maxsize=100)
    def get_file_logs(self, log_type, level, start_date, end_date):
        """Retrieve logs from file system with caching."""
        log_file_prefix = f"{log_type}_"
        log_file_suffix = ".log"
        log_directory = Config.LOG_FILE_PATH

        log_files = [
            os.path.join(log_directory, file)
            for file in os.listdir(log_directory)
            if file.startswith(log_file_prefix) and file.endswith(log_file_suffix)
        ]

        filtered_logs = []
        for log_file_path in log_files:
            try:
                with open(log_file_path, 'r') as log_file:
                    for log in log_file:
                        if level in log.upper():
                            if self.is_log_within_date_range(log, start_date, end_date):
                                filtered_logs.append(self.parse_log_entry(log))
            except Exception as e:
                logger.error(f"Error reading log file {log_file_path}: {str(e)}")
                continue

        return filtered_logs

    def get_db_logs(self, level, start_date, end_date, user_id,
                   resource_type, action, include_archived):
        """Retrieve logs from database."""
        query = AuditTrail.query

        # Apply filters
        if level:
            query = query.filter(AuditTrail.level == level)
        if start_date:
            query = query.filter(AuditTrail.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditTrail.timestamp <= end_date)
        if user_id:
            query = query.filter(AuditTrail.user_id == user_id)
        if resource_type:
            query = query.filter(AuditTrail.resource_type == resource_type)
        if action:
            query = query.filter(AuditTrail.action == action)
        if not include_archived:
            query = query.filter(AuditTrail.is_archived.is_(False))

        return [log.serialize() for log in query.all()]

    def parse_log_entry(self, log):
        """Parse a log entry into a structured format."""
        try:
            parts = log.strip().split(' - ')
            timestamp = datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S')
            level = parts[1]
            message = parts[2] if len(parts) > 2 else ''

            return {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }
        except Exception:
            return {'message': log.strip()}

    def is_log_within_date_range(self, log, start_date, end_date):
        """Check if a log entry falls within the specified date range."""
        try:
            log_date_str = log.split(' - ')[0]
            log_date = datetime.strptime(log_date_str, '%Y-%m-%d %H:%M:%S')

            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                if log_date.date() < start_date.date():
                    return False

            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                if log_date.date() > end_date.date():
                    return False

            return True
        except (ValueError, IndexError):
            return False

@log_ns.route('/archive')
class LogArchiveResource(Resource):
    @log_ns.doc(security='Bearer Auth')
    @jwt_required()
    def post(self):
        """Archive old logs (admin only)."""
        current_user = get_jwt_identity()

        if not check_role_permission(current_user):
            logger.warning(f"Unauthorized archive attempt by User ID {current_user['id']}")
            return {'message': 'Unauthorized'}, 403

        try:
            # Archive logs older than 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            old_logs = AuditTrail.query.filter(
                AuditTrail.timestamp < thirty_days_ago,
                AuditTrail.is_archived.is_(False)
            ).all()

            for log in old_logs:
                log.is_archived = True
                log.archived_at = datetime.utcnow()

            db.session.commit()

            # Log the archiving action
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ARCHIVE',
                resource_type='log',
                details=f"Archived {len(old_logs)} old logs",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': f'Successfully archived {len(old_logs)} logs'}, 200

        except Exception as e:
            logger.error(f"Error archiving logs: {str(e)}")
            db.session.rollback()
            return {'message': 'Error archiving logs'}, 500
