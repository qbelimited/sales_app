import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_restful import Api
from flask_swagger_ui import get_swaggerui_blueprint
from config import Config


# Disable OneDNN
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

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
from resources.auth_resource import AuthResource, AuthCallbackResource, LogoutResource
from resources.sales_resource import SaleResource
from resources.report_resource import ReportResource
from resources.admin_resource import AdminResource
from resources.manager_resource import ManagerSalesExecutiveResource, ManagerSalesExecutiveUpdateResource
from resources.dropdown_resource import DropdownResource
from resources.log_resource import LogResource
from resources.branch_resource import BranchResource
from resources.impact_product_resource import ImpactProductResource
from resources.paypoint_resource import PaypointResource
from resources.sales_executive_resource import SalesExecutiveResource
from resources.query_resource import QueryResource
from resources.query_response_resource import QueryResponseResource
from resources.access_resource import AccessResource
from resources.role_resource import RolesResource
from resources.audit_trail_resource import AuditTrailResource
from resources.under_inv_resource import UnderInvestigationResource
from resources.user_resource import UserResource

# Setting up routes with versioning
api_version = f"/api/{Config.API_VERSION}"

# Auth Routes
api.add_resource(AuthResource, f'{api_version}/auth/login')
api.add_resource(AuthCallbackResource, f'{api_version}/auth/callback')
api.add_resource(LogoutResource, f'{api_version}/auth/logout')

# CRUD Resources
api.add_resource(SaleResource, f'{api_version}/sales', f'{api_version}/sales/<int:sale_id>')
api.add_resource(ReportResource, f'{api_version}/reports', f'{api_version}/reports/<int:report_id>')
api.add_resource(AdminResource, f'{api_version}/admin')
api.add_resource(BranchResource, f'{api_version}/branches', f'{api_version}/branches/<int:branch_id>')
api.add_resource(ImpactProductResource, f'{api_version}/impact_products', f'{api_version}/impact_products/<int:product_id>')
api.add_resource(PaypointResource, f'{api_version}/paypoints', f'{api_version}/paypoints/<int:paypoint_id>')
api.add_resource(SalesExecutiveResource, f'{api_version}/sales_executives', f'{api_version}/sales_executives/<int:sales_executive_id>')
api.add_resource(QueryResource, f'{api_version}/queries', f'{api_version}/queries/<int:query_id>')
api.add_resource(QueryResponseResource, f'{api_version}/queries/<int:query_id>/responses')
api.add_resource(UnderInvestigationResource, f'{api_version}/under_investigations', f'{api_version}/under_investigations/<int:investigation_id>')
api.add_resource(UserResource, f'{api_version}/users', f'{api_version}/users/<int:user_id>')
api.add_resource(RolesResource, f'{api_version}/roles', f'{api_version}/roles/<int:role_id>')
api.add_resource(AccessResource, f'{api_version}/access')
api.add_resource(ManagerSalesExecutiveResource, f'{api_version}/manager/sales_executives')
api.add_resource(ManagerSalesExecutiveUpdateResource, f'{api_version}/manager/sales_executives/<int:executive_id>')

# Utility and Log Routes
api.add_resource(DropdownResource, f'{api_version}/dropdown')
api.add_resource(LogResource, f'{api_version}/logs')
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
