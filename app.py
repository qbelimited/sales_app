import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from flask_restx import Api
from logger import setup_logger
from extensions import db, jwt, migrate, cache

# Import all resource namespaces
from resources.auth_resource import auth_ns
from resources.sales_resource import sales_ns
from resources.report_resource import report_ns
from resources.admin_resource import admin_ns
from resources.help_resource import help_ns
from resources.dropdown_resource import dropdown_ns
from resources.log_resource import log_ns
from resources.branch_resource import branch_ns
from resources.impact_product_resource import impact_product_ns
from resources.paypoint_resource import paypoint_ns
from resources.sales_executive_resource import sales_executive_ns
from resources.user_resource import user_ns
from resources.audit_trail_resource import audit_ns
from resources.under_inv_resource import under_inv_ns
from resources.query_resource import query_ns
from resources.role_resource import role_ns
from resources.access_resource import access_ns
from resources.query_response_resource import query_response_ns
from resources.sales_performance_resource import sales_performance_ns
from resources.sales_target_resource import sales_target_ns
from resources.bank_resource import bank_ns
from resources.retention_resource import retention_ns
from resources.inception_resource import inception_ns

# Disable OneDNN for TensorFlow optimizations (if applicable)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
# os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_ENV'] = 'development'

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Determine the environment and load the appropriate config
# env = os.getenv('FLASK_ENV', 'production')
env = os.getenv('FLASK_ENV', 'development')
if env == 'development':
    app.config.from_object('config.DevelopmentConfig')
elif env == 'testing':
    app.config.from_object('config.TestConfig')
else:
    app.config.from_object('config.ProductionConfig')

# Disable strict trailing slash matching
app.config['STRICT_SLASHES'] = False

# Enable CORS dynamically based on the configuration
CORS(app, resources={
    r"/api/*": {
        "origins": app.config.get('CORS_ORIGINS', '*'),  # Get origins from config
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": app.config.get('SUPPORTS_CREDENTIALS', False)
    }
})

# Initialize Flask extensions with the app
db.init_app(app)
jwt.init_app(app)
migrate.init_app(app, db)
cache.init_app(app)

# Setup logging based on environment
logger = setup_logger(app)

# Define JWT Bearer token authorization for Swagger
authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT Bearer Token with prefix "Bearer "'
    }
}

# Initialize Flask-RESTX API with version prefix
api_version = app.config.get('API_VERSION', 'v1')
api = Api(app,
          version='1.0',
          title='Sales Recording API',
          doc=f'/api/{api_version}/docs',  # Removed trailing slash
          security='Bearer Auth',  # Apply global security
          authorizations=authorizations)  # Add Bearer Auth to the API

# Register Namespaces with versioned paths
api.add_namespace(auth_ns, path=f'/api/{api_version}/auth')
api.add_namespace(sales_ns, path=f'/api/{api_version}/sales')
api.add_namespace(report_ns, path=f'/api/{api_version}/reports')
api.add_namespace(admin_ns, path=f'/api/{api_version}/admin')
api.add_namespace(dropdown_ns, path=f'/api/{api_version}/dropdown')
api.add_namespace(log_ns, path=f'/api/{api_version}/logs')
api.add_namespace(branch_ns, path=f'/api/{api_version}/branches')
api.add_namespace(impact_product_ns, path=f'/api/{api_version}/impact_products')
api.add_namespace(paypoint_ns, path=f'/api/{api_version}/paypoints')
api.add_namespace(sales_executive_ns, path=f'/api/{api_version}/sales_executives')
api.add_namespace(query_ns, path=f'/api/{api_version}/queries')
api.add_namespace(query_response_ns, path=f'/api/{api_version}/query_responses')
api.add_namespace(access_ns, path=f'/api/{api_version}/access')
api.add_namespace(role_ns, path=f'/api/{api_version}/roles')
api.add_namespace(audit_ns, path=f'/api/{api_version}/audit_trail')
api.add_namespace(under_inv_ns, path=f'/api/{api_version}/under_investigation')
api.add_namespace(user_ns, path=f'/api/{api_version}/users')
api.add_namespace(sales_performance_ns, path=f'/api/{api_version}/sales_performance')
api.add_namespace(sales_target_ns, path=f'/api/{api_version}/sales_target')
api.add_namespace(bank_ns, path=f'/api/{api_version}/bank')
api.add_namespace(retention_ns, path=f'/api/{api_version}/retention')
api.add_namespace(inception_ns, path=f'/api/{api_version}/inceptions')
api.add_namespace(help_ns, path=f'/api/{api_version}/help')

# Serve the Swagger UI documentation at /api/v1/docs
swagger_ui_path = f'/api/{api_version}/docs'
swagger_json_path = f'/api/{api_version}/swagger.json'

# JWT callbacks for error handling
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"message": "The token has expired", "error": "token_expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"message": "Invalid token", "error": "token_invalid"}), 401

@jwt.unauthorized_loader
def unauthorized_callback(error):
    return jsonify({"message": "Request does not contain an access token", "error": "authorization_required"}), 401

@app.route(f"{swagger_json_path}")
def swagger_spec():
    """Serve the OpenAPI specification dynamically."""
    return api.__schema__

# Global error handler to log unhandled exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    """
    Handle uncaught exceptions and log them.

    Args:
        e (Exception): The exception that was raised.

    Returns:
        tuple: JSON response with error message and HTTP status code.
    """
    app.logger.error(f'Unhandled Exception: {e}', exc_info=True)
    return jsonify({"message": "An unexpected error occurred."}), 500

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=app.config.get('DEBUG', False))
