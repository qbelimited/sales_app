from flask import request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required
import csv
from io import StringIO  # Use StringIO to generate CSV in memory
from app import db
from models.sales_model import Sale
from models.user_model import User, Role
from models.sales_executive_model import SalesExecutive
from flask_restx import Namespace, Resource, fields
from sqlalchemy.orm import aliased  # Import aliased for handling multiple joins on the same table

# Define namespace for report-related operations
report_ns = Namespace('reports', description='Comprehensive Sales and Performance Report Generation')

# Define the model for Swagger documentation
report_model = report_ns.model('Report', {
    'filters': fields.Raw(description="Filters for the report")
})

# Define the report endpoint for generating sales reports
@report_ns.route('/sales')
@report_ns.doc(security='Bearer Auth')
@report_ns.expect(report_model, validate=True)
@report_ns.param('page', 'Page number for pagination', type='integer', default=1)
@report_ns.param('per_page', 'Number of items per page', type='integer', default=10)
@report_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
class SalesReportResource(Resource):
    @jwt_required()
    def post(self):
        try:
            data = request.get_json()
            filters = data.get('filters', {})
            sort_by = data.get('sort_by', 'created_at')
            sort_order = data.get('sort_order', 'asc')

            # Create aliases and build the query
            sales_manager_alias = aliased(User)
            user_alias = aliased(User)

            query = (
                Sale.query
                .join(user_alias, Sale.user_id == user_alias.id)
                .join(Role, user_alias.role_id == Role.id)
                .join(sales_manager_alias, Sale.sale_manager_id == sales_manager_alias.id)
                .join(SalesExecutive, Sale.sales_executive_id == SalesExecutive.id)
                .filter(Sale.is_deleted == False)
            )

            # Apply filters and sorting
            query = self.apply_filters(query, filters)
            query = self.apply_sorting(query, sort_by, sort_order)

            # Stream CSV as response
            return Response(
                stream_with_context(self.generate_csv(query)),
                mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=sales_report.csv"}
            )

        except Exception as e:
            print(f"An error occurred: {e}")  # Log error for debugging
            return jsonify({'message': 'Error fetching sales report', 'error': str(e)}), 500

    def apply_filters(self, query, filters):
        """Apply filters to the query."""
        from models.inception_model import Inception  # Import locally to avoid circular imports

        # Filter for date range
        if 'start_date' in filters and 'end_date' in filters:
            query = query.filter(Sale.created_at.between(filters['start_date'], filters['end_date']))

        if 'user_id' in filters:
            query = query.filter(Sale.user_id == filters['user_id'])

        if 'sale_manager_id' in filters:
            query = query.filter(Sale.sale_manager_id == filters['sale_manager_id'])

        if 'client_name' in filters:
            query = query.filter(Sale.client_name.ilike(f"%{filters['client_name']}%"))

        if 'status' in filters:
            query = query.filter(Sale.status == filters['status'])

        if 'collection_platform' in filters:
            query = query.filter(Sale.collection_platform == filters['collection_platform'])

        if 'bank_id' in filters:
            query = query.filter(Sale.bank_id == filters['bank_id'])

        if 'paypoint_id' in filters:
            query = query.filter(Sale.paypoint_id == filters['paypoint_id'])

        # Filter by user name
        if 'user_name' in filters:
            query = query.filter(User.name.ilike(f"%{filters['user_name']}%"))

        # Filter by role name
        if 'role_name' in filters:
            query = query.filter(Role.name.ilike(f"%{filters['role_name']}%"))

        # Combine Inception-related filters and join Inception only once if necessary
        if any(k in filters for k in ['inception_start_date', 'inception_end_date', 'inception_amount_min', 'inception_amount_max', 'inception_description']):
            query = query.join(Inception)
            if 'inception_start_date' in filters and 'inception_end_date' in filters:
                query = query.filter(Inception.received_at.between(filters['inception_start_date'], filters['inception_end_date']))

            if 'inception_amount_min' in filters:
                query = query.filter(Inception.amount_received >= filters['inception_amount_min'])

            if 'inception_amount_max' in filters:
                query = query.filter(Inception.amount_received <= filters['inception_amount_max'])

            if 'inception_description' in filters:
                query = query.filter(Inception.description.ilike(f"%{filters['inception_description']}%"))

        return query

    def apply_sorting(self, query, sort_by, sort_order):
        """Apply sorting to the query."""
        sort_column = getattr(Sale, sort_by, None)
        if sort_column is None:
            sort_column = Sale.created_at  # Default sorting column
        if sort_order == 'desc':
            query = query.order_by(db.desc(sort_column))
        else:
            query = query.order_by(db.asc(sort_column))
        return query

    def generate_csv(self, query):
        """Generate CSV row by row with dynamic headers."""
        # Fetch the first row to dynamically determine the headers
        first_row = query.first()
        if not first_row:
            # No data available, yield an empty CSV
            yield "No data available\n"
            return

        # Serialize the first row to get the headers dynamically
        first_row_dict = first_row.serialize()

        # Define the headers and columns to drop
        columns_to_drop = [
            'user_id', 'sale_manager', 'sales_executive_id', 'bank',
            'bank_branch', 'policy_type', 'is_deleted',
            'geolocation_latitude', 'geolocation_longitude',
            ]  # Specify the columns to drop
        dynamic_headers = [key for key in first_row_dict.keys() if key not in columns_to_drop] + [
            'sale_manager_name', 'inception_amount_received',
            'sales_executive_name', 'sales_executive_branch',
            'product_name', 'product_category', 'product_group',
            'bank_name', 'bank_branch_name'
        ]

        # Create a StringIO buffer to write CSV data in memory
        output = StringIO()
        writer = csv.writer(output)

        # Write the dynamic CSV headers
        writer.writerow(dynamic_headers)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Fetch the data in batches for efficiency
        for sale in query.yield_per(200):  # Adjust batch size as needed
            # Filter the sale_dict to remove unwanted columns
            sale_dict = {k: v for k, v in sale.serialize().items() if k not in columns_to_drop}
            sale_manager_data = sale.sale_manager.serialize() if sale.sale_manager else {}
            inception_data = sale.inceptions[0].amount_received if sale.inceptions else None
            sales_executive_name = sale.sales_executive.name if sale.sales_executive else None
            sales_executive_branch = sale.sales_executive.branches[0].name if sale.sales_executive.branches else None
            product_name = sale.policy_type.name if sale.policy_type else None
            product_category = sale.policy_type.category.name if sale.policy_type.category else None
            product_group = sale.policy_type.group if sale.policy_type.group else None
            bank_name = sale.bank.name if sale.bank else None
            bank_branch_name = sale.bank_branch.name if sale.bank_branch else None

            # Write a row to the CSV
            writer.writerow([
                *sale_dict.values(),  # Include all fields from the filtered sale
                sale_manager_data.get('name', 'N/A'),
                inception_data if inception_data else 'N/A',  # Include inception amount if available
                sales_executive_name if sales_executive_name else 'N/A',
                sales_executive_branch if sales_executive_branch else 'N/A',
                product_name if product_name else 'N/A',
                product_category if product_category else 'N/A',
                product_group if product_group else 'N/A',
                bank_name if bank_name else 'N/A',
                bank_branch_name if bank_branch_name else 'N/A',
            ])

            # Yield the CSV content row by row
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)  # Clear the buffer after each yield
