import os
import itertools
from flask_restx import Namespace, Resource
from config import Config
from flask import request
from models.audit_model import AuditTrail
from app import db, logger
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils import get_client_ip

# Define a namespace for log-related operations
log_ns = Namespace('log', description='Log access operations')

# Define parameters for Swagger documentation
log_param = log_ns.parser()
log_param.add_argument('type', type=str, required=False, default='general', help="Type of log: 'general', 'error', 'success'")
log_param.add_argument('level', type=str, required=False, default='INFO', help="Log level: 'INFO', 'WARNING', 'ERROR'")
log_param.add_argument('page', type=int, required=False, default=1, help="Page number for pagination")
log_param.add_argument('per_page', type=int, required=False, default=50, help="Number of log entries per page")
log_param.add_argument('start_date', type=str, required=False, help="Start date for log filter (YYYY-MM-DD)")
log_param.add_argument('end_date', type=str, required=False, help="End date for log filter (YYYY-MM-DD)")
log_param.add_argument('sort_order', type=str, required=False, default='desc', help="Sort order: 'asc' or 'desc'")

# Helper function to check role permissions
def check_role_permission(current_user):
    return current_user['role'].lower() == 'admin'

@log_ns.route('/')
class LogResource(Resource):
    @log_ns.doc(security='Bearer Auth')
    @log_ns.expect(log_param)
    @jwt_required()
    def get(self):
        """Retrieve logs based on type and level (admin only)."""
        current_user = get_jwt_identity()

        # Check if the user has admin role
        if not check_role_permission(current_user):
            return {'message': 'Unauthorized access'}, 403

        log_type = request.args.get('type', 'general').lower()  # 'general', 'error', 'success'
        level = request.args.get('level', 'INFO').upper()  # 'INFO', 'WARNING', 'ERROR'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_order = request.args.get('sort_order', 'desc').lower()  # 'asc' or 'desc'

        # Construct file pattern to match log files
        log_file_prefix = f"{log_type}_"
        log_file_suffix = ".log"
        log_directory = Config.LOG_FILE_PATH

        # Find all matching log files in the directory
        log_files = [
            os.path.join(log_directory, file)
            for file in os.listdir(log_directory)
            if file.startswith(log_file_prefix) and file.endswith(log_file_suffix)
        ]

        try:
            # Aggregate logs from multiple files using a generator
            filtered_logs = self.get_filtered_logs(log_files, level, start_date, end_date)

            # Sort logs by date (newest first or oldest first)
            sorted_logs = sorted(filtered_logs, key=lambda x: x.split(' ')[0], reverse=(sort_order == 'desc'))

            # Paginate the logs using islice for memory efficiency
            total_logs = len(sorted_logs)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_logs = list(itertools.islice(sorted_logs, start_idx, end_idx))

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='log',
                resource_id=None,
                details=f"Accessed {log_type} logs with level {level}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            total_pages = (total_logs + per_page - 1) // per_page  # Calculate total pages

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

    def get_filtered_logs(self, log_files, level, start_date, end_date):
        """Retrieve logs filtered by log level and date range from multiple files."""
        filtered_logs = []
        for log_file_path in log_files:
            try:
                with open(log_file_path, 'r') as log_file:
                    for log in log_file:
                        if level in log.upper():
                            if self.is_log_within_date_range(log, start_date, end_date):
                                filtered_logs.append(log)
            except Exception as e:
                logger.error(f"Error filtering logs from {log_file_path}: {str(e)}")
                continue
        return filtered_logs

    def is_log_within_date_range(self, log, start_date, end_date):
        """Check if a log entry falls within the specified date range."""
        try:
            log_date_str = log.split(' ')[0]  # Assuming the log date is the first field
            log_date = datetime.strptime(log_date_str, '%Y-%m-%d')

            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                if log_date < start_date:
                    return False

            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                if log_date > end_date:
                    return False

            return True
        except (ValueError, IndexError):
            # If log doesn't have a valid date, ignore the log
            return False
