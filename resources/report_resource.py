from flask import request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv
from io import StringIO
from app import db, logger
from models.sales_model import Sale
from models.user_model import User, Role
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from flask_restx import Namespace, Resource, fields
from sqlalchemy.orm import aliased
from sqlalchemy import func
from datetime import datetime

# Utility function to get client IP
def get_client_ip():
    """Retrieve the client's IP address."""
    return request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

# Define namespace for report-related operations
report_ns = Namespace('reports', description='Comprehensive Sales and Performance Report Generation')

# Define the model for Swagger documentation
report_model = report_ns.model('Report', {
    'filters': fields.Raw(description="Filters for the report"),
    'aggregate_by': fields.String(description="Field to aggregate by (e.g., bank_id, product_type, branch)"),
})

@report_ns.route('/sales')
@report_ns.doc(security='Bearer Auth')
@report_ns.expect(report_model, validate=True)
@report_ns.param('page', 'Page number for pagination', type='integer', default=1)
@report_ns.param('per_page', 'Number of items per page', type='integer', default=10)
@report_ns.param('sort_by', 'Sort by field (e.g., created_at, name)', type='string', default='created_at')
@report_ns.param('sort_order', 'Sort order (asc or desc)', type='string', default='desc')
class SalesReportResource(Resource):
    @jwt_required()
    def post(self):
        """Generate a sales report based on specified filters and pagination."""
        try:
            current_user = get_jwt_identity()
            data = request.get_json()
            filters = data.get('filters', {})
            aggregate_by = data.get('aggregate_by', None)
            sort_by = data.get('sort_by', 'created_at')
            sort_order = data.get('sort_order', 'asc')
            page = request.args.get('page', type=int, default=1)
            per_page = request.args.get('per_page', type=int, default=10)

            # Validate input parameters
            validation_error = self.validate_parameters(sort_order, filters)
            if validation_error:
                return validation_error  # Should return a JSON response

            # Build and execute the query
            query = self.build_sales_query(filters)
            query = self.apply_filters(query, filters)
            query = self.apply_sorting(query, sort_by, sort_order)

            # Execute the query to get sales data
            paginated_query = query.paginate(page=page, per_page=per_page, error_out=False)

            # Get aggregation results if needed
            aggregation_results = {}
            if aggregate_by:
                aggregation_results = self.calculate_aggregates(query, aggregate_by)

            # Log the action to the audit trail
            self.log_audit(current_user['id'], filters)

            # Stream the CSV response
            response = self.stream_csv_response(paginated_query.items, aggregation_results)

            # Include pagination metadata in the response
            response.headers['X-Total-Pages'] = paginated_query.pages
            response.headers['X-Total-Records'] = paginated_query.total

            return response  # This should return a Response object for CSV

        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return self.create_error_response('Error fetching sales report', str(e))

    def validate_parameters(self, sort_order, filters):
        """Validate input parameters for the report generation."""
        if sort_order not in ['asc', 'desc']:
            return jsonify({'message': 'Invalid sort_order. Use "asc" or "desc".'}), 400
        return None

    def build_sales_query(self, filters):
        """Build the base query for sales."""
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
        return query

    def log_audit(self, user_id, filters):
        """Log the report generation action to the audit trail."""
        audit = AuditTrail(
            user_id=user_id,
            action='GENERATE_REPORT',
            resource_type='sales_report',
            resource_id=None,
            details=f"Generated Sales Report with filters: {filters}",
            ip_address=get_client_ip(),
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit)
        db.session.commit()
        logger.info(f"Sales report generated by user {user_id} with filters: {filters}")

    def stream_csv_response(self, sales, aggregation_results):
        """Stream CSV response with sales data."""
        response = Response(
            stream_with_context(self.generate_csv(sales)),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=sales_report.csv"}
        )

        # Include aggregation results in response headers if available
        for key, value in aggregation_results.items():
            response.headers[f'X-Aggregate-{key}'] = value

        return response  # This should be a valid CSV response

    def create_error_response(self, message, error):
        """Create a standardized error response."""
        return jsonify({'message': message, 'error': error}), 500

    def calculate_aggregates(self, query, aggregate_by):
        """Calculate total premium and counts based on the specified field with pagination."""
        if aggregate_by not in [
            'sale_manager_name', 'sales_executive_name', 'sales_executive_branch',
            'product_name', 'product_category', 'product_group',
            'bank_name', 'bank_branch_name', 'paypoint_name', 'source_type',
            'collection_platform', 'status', 'customer_called', 'momo_first_premium',
        ]:
            return {'message': 'Invalid aggregate field provided.'}

        results = query.with_entities(
            self.get_aggregate_field(aggregate_by),
            func.sum(Sale.amount).label('total_premium'),
            func.count(Sale.id).label('total_count')
        ).group_by(self.get_aggregate_field(aggregate_by)).all()

        aggregation_results = {result[0]: {'total_premium': result.total_premium, 'total_count': result.total_count} for result in results}
        return aggregation_results

    def get_aggregate_field(self, aggregate_by):
        """Return the SQLAlchemy field for the specified aggregation type."""
        aggregate_fields = {
            'sale_manager_name': Sale.sale_manager.name,
            'sales_executive_name': Sale.sales_executive.name,
            'sales_executive_branch': Sale.sales_executive.branches[0].name,
            'product_name': Sale.policy_type.name,
            'product_category': Sale.policy_type.category.name,
            'product_group': Sale.policy_type.group,
            'bank_name': Sale.bank.name,
            'bank_branch_name': Sale.bank_branch.name,
            'paypoint_name': Sale.paypoint.name,
            'source_type': Sale.source_type,
            'collection_platform': Sale.collection_platform,
            'status': Sale.status,
            'customer_called': Sale.customer_called,
            'momo_first_premium': Sale.momo_first_premium,
        }
        return aggregate_fields.get(aggregate_by)

    def apply_filters(self, query, filters):
        """Apply filters to the query based on the provided filter criteria."""
        from models.inception_model import Inception

        # Filter for date range
        if 'start_date' in filters and 'end_date' in filters:
            try:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(Sale.created_at.between(start_date, end_date))
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD for start_date and end_date.'}), 400

        # Apply additional filters based on user input
        filter_fields = [
            ('user_id', Sale.user_id),
            ('sale_manager_id', Sale.sale_manager_id),
            ('client_name', Sale.client_name.ilike(f"%{filters.get('client_name', '')}%")),
            ('status', Sale.status),
            ('collection_platform', Sale.collection_platform),
            ('bank_id', Sale.bank_id),
            ('paypoint_id', Sale.paypoint_id),
            ('user_name', User.name.ilike(f"%{filters.get('user_name', '')}%")),
            ('role_name', Role.name.ilike(f"%{filters.get('role_name', '')}%")),
        ]

        for key, field in filter_fields:
            if key in filters:
                query = query.filter(field == filters[key]) if key not in ['client_name', 'user_name', 'role_name'] else query.filter(field)

        # Inception-related filters
        if any(k in filters for k in ['inception_start_date', 'inception_end_date', 'inception_amount_min', 'inception_amount_max', 'inception_description']):
            query = query.join(Inception)
            if 'inception_start_date' in filters and 'inception_end_date' in filters:
                try:
                    inception_start_date = datetime.strptime(filters['inception_start_date'], '%Y-%m-%d').date()
                    inception_end_date = datetime.strptime(filters['inception_end_date'], '%Y-%m-%d').date()
                    query = query.filter(Inception.received_at.between(inception_start_date, inception_end_date))
                except ValueError:
                    return jsonify({'message': 'Invalid inception date format. Use YYYY-MM-DD for inception_start_date and inception_end_date.'}), 400

            if 'inception_amount_min' in filters:
                query = query.filter(Inception.amount_received >= filters['inception_amount_min'])

            if 'inception_amount_max' in filters:
                query = query.filter(Inception.amount_received <= filters['inception_amount_max'])

            if 'inception_description' in filters:
                query = query.filter(Inception.description.ilike(f"%{filters['inception_description']}%"))

        return query

    def apply_sorting(self, query, sort_by, sort_order):
        """Apply sorting to the query based on the specified field and order."""
        sort_column = getattr(Sale, sort_by, None)
        if sort_column is None:
            logger.warning(f"Invalid sort_by parameter: {sort_by}. Defaulting to created_at.")
            sort_column = Sale.created_at  # Default sorting column
        query = query.order_by(db.desc(sort_column) if sort_order == 'desc' else db.asc(sort_column))
        return query

    def generate_csv(self, sales):
        """Generate CSV row by row with dynamic headers."""
        if not sales:
            yield "No data available\n"
            return

        first_row_dict = sales[0].serialize()
        columns_to_drop = [
            'user_id', 'sale_manager', 'sales_executive_id',
            'bank_branch', 'policy_type',
            'geolocation_latitude', 'geolocation_longitude',
            'paypoint', 'bank',
        ]

        dynamic_headers = [key for key in first_row_dict.keys() if key not in columns_to_drop] + [
            'sales_id', 'sale_manager_name', 'inception_amount_received',
            'sales_executive_code', 'sales_executive_name', 'sales_executive_branch',
            'product_name', 'product_category', 'product_group',
            'bank_name', 'bank_branch_name', 'paypoint_name',
        ]

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(dynamic_headers)  # Write the header row
        yield output.getvalue()  # Yield the headers
        output.seek(0)
        output.truncate(0)

        # Write each sale's data to the CSV
        for sale in sales:
            sale_dict = {k: v for k, v in sale.serialize().items() if k not in columns_to_drop}
            sales_id = sale.id if sale.id else None
            sale_manager_data = sale.sale_manager.serialize() if sale.sale_manager else {}
            inception_data = sale.inceptions[0].amount_received if sale.inceptions else None
            sales_executive_code = sale.sales_executive.code if sale.sales_executive else None
            sales_executive_name = sale.sales_executive.name if sale.sales_executive else None
            sales_executive_branch = sale.sales_executive.branches[0].name if sale.sales_executive.branches else None
            product_name = sale.policy_type.name if sale.policy_type else None
            product_category = sale.policy_type.category.name if sale.policy_type else None
            product_group = sale.policy_type.group if sale.policy_type.group else None
            bank_name = sale.bank.name if sale.bank else None
            bank_branch_name = sale.bank_branch.name if sale.bank_branch else None
            paypoint_name = sale.paypoint.name if sale.paypoint else None

            # Write the row for the current sale
            writer.writerow([
                *sale_dict.values(),
                sales_id if sales_id else 'N/A',
                sale_manager_data.get('name', 'N/A'),
                inception_data if inception_data else 'N/A',
                sales_executive_code if sales_executive_code else 'N/A',
                sales_executive_name if sales_executive_name else 'N/A',
                sales_executive_branch if sales_executive_branch else 'N/A',
                product_name if product_name else 'N/A',
                product_category if product_category else 'N/A',
                product_group if product_group else 'N/A',
                bank_name if bank_name else 'N/A',
                bank_branch_name if bank_branch_name else 'N/A',
                paypoint_name if paypoint_name else 'N/A',
            ])

            yield output.getvalue()  # Yield the current CSV data
            output.seek(0)
            output.truncate(0)  # Clear the output for the next row
