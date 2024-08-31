from flask_restful import Resource
import os
from config import Config

class LogResource(Resource):
    def get(self):
        log_type = request.args.get('type', 'general')  # 'general', 'error', 'success'
        level = request.args.get('level', 'INFO')  # 'INFO', 'WARNING', 'ERROR'

        log_file_map = {
            'general': 'general.log',
            'error': 'error.log',
            'success': 'success.log'
        }

        log_file_path = os.path.join(Config.LOG_FILE_PATH, log_file_map.get(log_type, 'general.log'))

        with open(log_file_path, 'r') as log_file:
            logs = log_file.readlines()

        # Optionally filter by log level
        filtered_logs = [log for log in logs if f"{level}" in log]

        return {'logs': filtered_logs}, 200
