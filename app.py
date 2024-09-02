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
migrate = Migrate(app, db)
api = Api(app)

from models.user_model import User, Role
from models.sales_model import Sale
from models.bank_model import Bank, BankBranch
from models.paypoint_model import Paypoint
from models.impact_product_model import ImpactProduct
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from models.under_investigation_model import UnderInvestigation
from models.branch_model import Branch

# Import resources and add routes
from resources.auth_resource import AuthResource, AuthCallbackResource, LogoutResource
from resources.sales_resource import SaleResource
from resources.report_resource import ReportResource
from resources.admin_resource import AdminResource
from resources.manager_resource import ManagerResource
from resources.dropdown_resource import DropdownResource
from resources.log_resource import LogResource
from resources.branch_resource import BranchResource
from resources.impact_product_resource import ImpactProductResource
from resources.paypoint_resource import PaypointResource
from resources.sales_executive_resource import SalesExecutiveResource
from resources.user_resource import UserResource
from resources.audit_trail_resource import AuditTrailResource

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
api.add_resource(BranchResource, f'{api_version}/branches', f'{api_version}/branches/<int:branch_id>')
api.add_resource(ImpactProductResource, f'{api_version}/impact_products')
api.add_resource(PaypointResource, f'{api_version}/paypoints')
api.add_resource(SalesExecutiveResource, f'{api_version}/sales_executives')
api.add_resource(UserResource, f'{api_version}/users')
api.add_resource(AuditTrailResource, f'{api_version}/audit_trails')

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
