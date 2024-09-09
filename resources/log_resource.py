import os
from flask_restx import Namespace, Resource
from config import Config
from flask import request, jsonify
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

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

        log_type = request.args.get('type', 'general')  # 'general', 'error', 'success'
        level = request.args.get('level', 'INFO')  # 'INFO', 'WARNING', 'ERROR'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        log_file_map = {
            'general': 'general.log',
            'error': 'error.log',
            'success': 'success.log'
        }

        log_file_path = os.path.join(Config.LOG_FILE_PATH, log_file_map.get(log_type, 'general.log'))

        try:
            # Check if log file exists
            if not os.path.exists(log_file_path):
                return {'message': f'Log file not found: {log_file_map.get(log_type, "general.log")}'}, 404

            with open(log_file_path, 'r') as log_file:
                logs = log_file.readlines()

            # Filter logs by log level
            filtered_logs = [log for log in logs if f"{level}" in log]

            # Filter logs by date range if provided
            if start_date or end_date:
                filtered_logs = self.filter_logs_by_date(filtered_logs, start_date, end_date)

            # Paginate the logs
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_logs = filtered_logs[start_idx:end_idx]

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='log',
                resource_id=None,
                details=f"Accessed {log_type} logs with level {level}"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'logs': paginated_logs,
                'total_logs': len(filtered_logs),
                'current_page': page,
                'per_page': per_page
            }, 200

        except Exception as e:
            logger.error(f"Error retrieving logs: {str(e)}")
            return {'message': str(e)}, 500

    @staticmethod
    def filter_logs_by_date(logs, start_date, end_date):
        """Filter logs based on a date range."""
        if not start_date and not end_date:
            return logs

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        except ValueError:
            return logs  # If the date format is incorrect, skip filtering by date

        filtered_logs = []
        for log in logs:
            log_date_str = log.split(' ')[0]  # Assuming the log date is the first field
            try:
                log_date = datetime.strptime(log_date_str, '%Y-%m-%d')
                if (not start_date or log_date >= start_date) and (not end_date or log_date <= end_date):
                    filtered_logs.append(log)
            except ValueError:
                continue  # Skip logs without a valid date format
        return filtered_logs
