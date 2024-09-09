import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from flask_restx import Api
from logger import setup_logger

# Disable OneDNN
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.config.from_object('config.Config')

# Enable CORS for the app
CORS(app)

# Enable CORS with custom settings
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Initialize database, JWT, migration, and API
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Setup logging
logger = setup_logger(app)

# Initialize Flask-RESTX API with version prefix
api_version = 'v1'  # Define the API version
api = Api(app, version='1.0', title='Sales Recording API', doc=f'/api/{api_version}/docs')

# Import Models
from models.user_model import User, Role
from models.sales_model import Sale
from models.bank_model import Bank, BankBranch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from models.under_investigation_model import UnderInvestigation
from models.branch_model import Branch
from models.query_model import Query, QueryResponse
from models.report_model import Report
from models.user_session_model import UserSession

# Import Resources
from resources.auth_resource import auth_ns
from resources.sales_resource import sales_ns
from resources.report_resource import report_ns
from resources.admin_resource import admin_ns
from resources.manager_resource import manager_ns
from resources.dropdown_resource import dropdown_ns
from resources.log_resource import log_ns
from resources.branch_resource import branch_ns
from resources.impact_product_resource import impact_product_ns
from resources.paypoint_resource import paypoint_ns
from resources.sales_executive_resource import sales_executive_ns
from resources.query_resource import query_ns
from resources.query_response_resource import query_response_ns
from resources.access_resource import access_ns
from resources.role_resource import role_ns
from resources.audit_trail_resource import audit_ns
from resources.under_inv_resource import under_inv_ns
from resources.user_resource import user_ns

# Register Namespaces with versioned paths
api.add_namespace(auth_ns, path=f'/api/{api_version}/auth')
api.add_namespace(sales_ns, path=f'/api/{api_version}/sales')
api.add_namespace(report_ns, path=f'/api/{api_version}/reports')
api.add_namespace(admin_ns, path=f'/api/{api_version}/admin')
api.add_namespace(manager_ns, path=f'/api/{api_version}/manager')
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

# Serve the Swagger UI documentation at /api/v1/docs
swagger_ui_path = f'/api/{api_version}/docs'
swagger_json_path = f'/api/{api_version}/swagger.json'

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
    return {"message": "An unexpected error occurred."}, 500

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
