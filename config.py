import os
import logging
import logging.config


# Base configuration class
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cache configuration
    CACHE_TYPE = 'SimpleCache'  # Default to SimpleCache
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default timeout
    CACHE_THRESHOLD = 1000  # Maximum number of items to store
    CACHE_KEY_PREFIX = 'sales_app_'
    CACHE_NO_NULL_WARNING = True

    # Optimized database connection pooling for high transaction volume
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 50,  # Increased pool size for more concurrent connections
        'max_overflow': 30,  # Increased overflow for peak loads
        'pool_timeout': 30,
        'pool_recycle': 3600,  # Recycle connections every hour
        'pool_pre_ping': True,  # Enable connection health checks
        'echo': False  # Disable SQL logging for better performance
    }

    # SQLAlchemy settings
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_MAX_OVERFLOW = 30
    SQLALCHEMY_POOL_SIZE = 50

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')
    API_VERSION = os.getenv('API_VERSION', 'v1')

    # Default log file path and creation
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/')
    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)

    # Common Logging configuration
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


# Development Configuration
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        'sqlite:///dev.db'
    )
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000"
    ]
    DEBUG = True
    TESTING = True

    # Development cache configuration
    CACHE_DEFAULT_TIMEOUT = 60  # 1 minute in development
    CACHE_THRESHOLD = 500
    CACHE_KEY_PREFIX = 'sales_app_dev_'

    # Override logging for development (stdout, more verbose)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'general_file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(Config.LOG_FILE_PATH, 'dev_general.log'),
                'formatter': 'default',
            },
            'error_file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(Config.LOG_FILE_PATH, 'dev_error.log'),
                'formatter': 'default',
                'level': 'ERROR',
            },
        },
        'loggers': {
            'general': {
                'handlers': ['console', 'general_file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'error': {
                'handlers': ['console', 'error_file'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }


# Production Configuration
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://root:Sales_Password1@localhost/sales_app_db'
    )
    CORS_ORIGINS = [
        "https://salesapp.impactlife.com.gh",
        "https://api.salesapp.impactlife.com.gh",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    DEBUG = False
    TESTING = False

    # Production cache configuration
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes in production
    CACHE_KEY_PREFIX = 'sales_app_prod_'


# Test Configuration (Same as Development but with a separate test database)
class TestConfig(DevelopmentConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///test.db')
    TESTING = True
    DEBUG = True

    # You can disable or minimize logging during tests to focus on test outputs
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,  # Disable logging for faster test runs
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },
        'loggers': {
            'general': {
                'handlers': ['console'],
                'level': 'WARNING',  # Log only warnings and errors during tests
                'propagate': True,
            },
            'error': {
                'handlers': ['console'],
                'level': 'ERROR',
                'propagate': True,
            },
        },
    }


# Initialize logging configuration
def setup_logging():
    env = os.getenv('FLASK_ENV', 'production')  # Default to production
    if env == 'development':
        logging.config.dictConfig(DevelopmentConfig.LOGGING)
    elif env == 'testing':
        logging.config.dictConfig(TestConfig.LOGGING)
    else:
        logging.config.dictConfig(ProductionConfig.LOGGING)


# Ensure logging is set up at module load
logging.config.dictConfig(Config.LOGGING)
