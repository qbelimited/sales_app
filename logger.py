import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(app):
    """
    Configures logging for the Flask application.

    Args:
        app (Flask): The Flask application instance.
    """
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Get the current date to use in filenames
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Define log format
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )

    # Remove default handlers to prevent duplicate logs
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # Set the logging level based on environment
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO

    # ---------------- General Log ----------------
    general_log_file = f'logs/general_{current_date}.log'
    general_handler = RotatingFileHandler(
        general_log_file, maxBytes=1000000, backupCount=10
    )
    general_handler.setLevel(log_level)
    general_handler.setFormatter(formatter)

    # ---------------- Success Log ----------------
    success_log_file = f'logs/success_{current_date}.log'
    success_handler = RotatingFileHandler(
        success_log_file, maxBytes=1000000, backupCount=10
    )
    success_handler.setLevel(logging.INFO)  # Logs only INFO and SUCCESS levels
    success_handler.setFormatter(formatter)

    # ---------------- Error Log ----------------
    error_log_file = f'logs/error_{current_date}.log'
    error_handler = RotatingFileHandler(
        error_log_file, maxBytes=1000000, backupCount=10
    )
    error_handler.setLevel(logging.ERROR)  # Logs ERROR and CRITICAL levels
    error_handler.setFormatter(formatter)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Add handlers to the app's logger
    app.logger.addHandler(general_handler)  # General log
    app.logger.addHandler(success_handler)  # Success log
    app.logger.addHandler(error_handler)    # Error log
    app.logger.addHandler(console_handler)  # Console log

    # Set the overall logging level
    app.logger.setLevel(log_level)

    return app.logger
