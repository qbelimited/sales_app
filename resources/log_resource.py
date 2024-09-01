import os
from flask_restful import Resource
from config import Config
from flask import request, jsonify
from models.audit_model import AuditTrail
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity

class LogResource(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        log_type = request.args.get('type', 'general')  # 'general', 'error', 'success'
        level = request.args.get('level', 'INFO')  # 'INFO', 'WARNING', 'ERROR'

        log_file_map = {
            'general': 'general.log',
            'error': 'error.log',
            'success': 'success.log'
        }

        log_file_path = os.path.join(Config.LOG_FILE_PATH, log_file_map.get(log_type, 'general.log'))

        try:
            with open(log_file_path, 'r') as log_file:
                logs = log_file.readlines()

            # Optionally filter by log level
            filtered_logs = [log for log in logs if f"{level}" in log]

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

            return {'logs': filtered_logs}, 200

        except FileNotFoundError:
            return {'message': f'Log file not found: {log_file_map.get(log_type, "general.log")}'}, 404
        except Exception as e:
            return {'message': str(e)}, 500
