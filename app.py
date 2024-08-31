from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

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

# Setting up routes
api.add_resource(AuthResource, '/auth/login')
api.add_resource(AuthCallbackResource, '/auth/callback')
api.add_resource(LogoutResource, '/auth/logout')
api.add_resource(SaleResource, '/sales', '/sales/<int:sale_id>')
api.add_resource(ReportResource, '/reports')
api.add_resource(AdminResource, '/admin')
api.add_resource(ManagerResource, '/manager')
api.add_resource(DropdownResource, '/dropdown')
api.add_resource(LogResource, '/logs')

if __name__ == "__main__":
    app.run(debug=True)
