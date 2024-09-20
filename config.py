import os
import logging
import logging.config

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://root:Sales_Password1@localhost/sales_app_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
    API_VERSION = os.getenv('API_VERSION', 'v1')  # Added API versioning
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/')

    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
        },
        'handlers': {
            'general_file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(LOG_FILE_PATH, 'general.log'),
                'formatter': 'default',
            },
            'error_file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(LOG_FILE_PATH, 'error.log'),
                'formatter': 'default',
                'level': 'ERROR',
            },
            'success_file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(LOG_FILE_PATH, 'success.log'),
                'formatter': 'default',
                'level': 'INFO',
            },
        },
        'loggers': {
            'general': {
                'handlers': ['general_file'],
                'level': 'INFO',
                'propagate': True,
            },
            'error': {
                'handlers': ['error_file'],
                'level': 'ERROR',
                'propagate': True,
            },
            'success': {
                'handlers': ['success_file'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }

logging.config.dictConfig(Config.LOGGING)
