import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_restful import Api
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config

# Load environment variables
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database, JWT, migration, and API
db = SQLAlchemy(app)
jwt = JWTManager(app)
api = Api(app)
migrate = Migrate(app, db)

# Importing models so that Flask-Migrate can detect changes
from models.user_model import User
from models.sales_model import Sale
from models.sales_executive_model import SalesExecutive
from models.bank_model import Bank, Branch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.audit_model import AuditTrail

# Importing resources and adding routes
from resources.auth_resource import AuthResource, AuthCallbackResource, LogoutResource
from resources.sales_resource import SaleResource
from resources.report_resource import ReportResource
from resources.admin_resource import AdminResource
from resources.manager_resource import ManagerResource
from resources.dropdown_resource import DropdownResource
from resources.log_resource import LogResource

# Setting up routes with versioning
api_version = f"/api/{Config.API_VERSION}"

api.add_resource(AuthResource, f'{api_version}/auth/login')
api.add_resource(AuthCallbackResource, f'{api_version}/auth/callback')
api.add_resource(LogoutResource, f'{api_version}/auth/logout')
api.add_resource(SaleResource, f'{api_version}/sales', f'{api_version}/sales/<int:sale_id>')
api.add_resource(ReportResource, f'{api_version}/reports')
api.add_resource(AdminResource, f'{api_version}/admin')
api.add_resource(ManagerResource, f'{api_version}/manager')
api.add_resource(DropdownResource, f'{api_version}/dropdown')
api.add_resource(LogResource, f'{api_version}/logs')

# Swagger UI setup
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'  # URL for exposing Swagger JSON

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Sales Recording API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Run the Flask application
if __name__ == "__main__":
    app.run(debug=True)
