from flask import request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
import csv
from io import StringIO
from extensions import db
from models.sales_model import Sale
from models.user_model import User, Role
from models.sales_executive_model import SalesExecutive
from models.audit_model import AuditTrail
from models.report_model import (
    Report, ReportType, ReportSchedule, ReportAccessLevel, CustomReport
)
from flask_restx import Namespace, Resource, fields
from sqlalchemy.orm import aliased
from sqlalchemy import func
from datetime import datetime
from utils import get_client_ip

# Define namespace for report-related operations
report_ns = Namespace(
    'reports',
    description='Comprehensive Sales and Performance Report Generation'
)

# Define models for Swagger documentation
report_model = report_ns.model('Report', {
    'report_type': fields.String(
        required=True,
        description='Type of report to generate',
        enum=[rt.value for rt in ReportType]
    ),
    'filters': fields.Raw(description="Filters for the report"),
    'aggregate_by': fields.String(description="Field to aggregate by"),
    'format': fields.String(
        description="Output format (csv, pdf, excel)",
        default='csv'
    ),
    'schedule': fields.String(
        description="Schedule for report generation",
        enum=[s.value for s in ReportSchedule]
    ),
    'access_level': fields.String(
        description="Access level for the report",
        enum=[al.value for al in ReportAccessLevel]
    ),
    'allowed_roles': fields.List(
        fields.Integer,
        description="List of role IDs with access"
    ),
    'name': fields.String(description="Name of the report"),
    'description': fields.String(description="Description of the report")
})

@report_ns.route('/')
class ReportListResource(Resource):
    @jwt_required()
    def get(self):
        """Get a list of available reports."""
        current_user = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        try:
            reports = Report.get_user_reports(
                current_user['id'],
                current_user.get('role_id'),
                page,
                per_page,
                sort_by,
                sort_order
            )
            return {
                'reports': [report.serialize() for report in reports.items],
                'total': reports.total,
                'pages': reports.pages,
                'current_page': reports.page
            }, 200
        except Exception as e:
            logger.error(f"Error fetching reports: {str(e)}")
            return {'message': 'Error fetching reports'}, 500

    @jwt_required()
    @report_ns.expect(report_model)
    def post(self):
        """Create a new report configuration."""
        current_user = get_jwt_identity()
        data = request.json

        try:
            # Validate report type
            if 'report_type' not in data:
                return {'message': 'Report type is required'}, 400
            try:
                ReportType(data['report_type'])
            except ValueError:
                return {'message': 'Invalid report type'}, 400

            # Create new report
            report_name = f"{data['report_type']} Report"
            new_report = Report(
                user_id=current_user['id'],
                report_type=data['report_type'],
                name=data.get('name', report_name),
                description=data.get('description'),
                parameters=data.get('filters', {}),
                schedule=data.get('schedule', ReportSchedule.MANUAL.value),
                access_level=data.get(
                    'access_level',
                    ReportAccessLevel.PRIVATE.value
                ),
                allowed_roles=data.get('allowed_roles'),
                next_run_at=(
                    datetime.utcnow()
                    if data.get('schedule') != ReportSchedule.MANUAL.value
                    else None
                )
            )
            db.session.add(new_report)
            db.session.commit()

            # Log the creation to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='CREATE',
                resource_type='report',
                resource_id=new_report.id,
                details=f"Created new report: {new_report.name}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return new_report.serialize(), 201
        except Exception as e:
            logger.error(f"Error creating report: {str(e)}")
            return {'message': 'Error creating report'}, 500

@report_ns.route('/<int:report_id>')
class ReportResource(Resource):
    @jwt_required()
    def get(self, report_id):
        """Get a specific report configuration."""
        current_user = get_jwt_identity()

        try:
            report = Report.query.filter_by(
                id=report_id,
                is_deleted=False
            ).first()
            if not report:
                return {'message': 'Report not found'}, 404

            has_access = report.has_access(
                current_user['id'],
                current_user.get('role_id')
            )
            if not has_access:
                return {'message': 'Unauthorized access'}, 403

            return report.serialize(), 200
        except Exception as e:
            logger.error(f"Error fetching report: {str(e)}")
            return {'message': 'Error fetching report'}, 500

    @jwt_required()
    @report_ns.expect(report_model)
    def put(self, report_id):
        """Update a report configuration."""
        current_user = get_jwt_identity()
        data = request.json

        try:
            report = Report.query.filter_by(
                id=report_id,
                is_deleted=False
            ).first()
            if not report:
                return {'message': 'Report not found'}, 404

            has_access = report.has_access(
                current_user['id'],
                current_user.get('role_id')
            )
            if not has_access:
                return {'message': 'Unauthorized access'}, 403

            # Update report fields
            if 'report_type' in data:
                try:
                    ReportType(data['report_type'])
                    report.report_type = data['report_type']
                except ValueError:
                    return {'message': 'Invalid report type'}, 400

            if 'name' in data:
                report.name = data['name']
            if 'description' in data:
                report.description = data['description']
            if 'parameters' in data:
                report.parameters = data['parameters']
            if 'schedule' in data:
                try:
                    ReportSchedule(data['schedule'])
                    report.schedule = data['schedule']
                    report.next_run_at = (
                        datetime.utcnow()
                        if data['schedule'] != ReportSchedule.MANUAL.value
                        else None
                    )
                except ValueError:
                    return {'message': 'Invalid schedule'}, 400
            if 'access_level' in data:
                try:
                    ReportAccessLevel(data['access_level'])
                    report.access_level = data['access_level']
                except ValueError:
                    return {'message': 'Invalid access level'}, 400
            if 'allowed_roles' in data:
                report.allowed_roles = data['allowed_roles']

            report.updated_at = datetime.utcnow()
            db.session.commit()

            # Log the update to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='UPDATE',
                resource_type='report',
                resource_id=report.id,
                details=f"Updated report: {report.name}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return report.serialize(), 200
        except Exception as e:
            logger.error(f"Error updating report: {str(e)}")
            return {'message': 'Error updating report'}, 500

    @jwt_required()
    def delete(self, report_id):
        """Soft delete a report configuration."""
        current_user = get_jwt_identity()

        try:
            report = Report.query.filter_by(
                id=report_id,
                is_deleted=False
            ).first()
            if not report:
                return {'message': 'Report not found'}, 404

            has_access = report.has_access(
                current_user['id'],
                current_user.get('role_id')
            )
            if not has_access:
                return {'message': 'Unauthorized access'}, 403

            Report.soft_delete(report_id)

            # Log the deletion to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='DELETE',
                resource_type='report',
                resource_id=report.id,
                details=f"Deleted report: {report.name}",
                ip_address=get_client_ip(),
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit)
            db.session.commit()

            return {'message': 'Report deleted successfully'}, 200
        except Exception as e:
            logger.error(f"Error deleting report: {str(e)}")
            return {'message': 'Error deleting report'}, 500

@report_ns.route('/<int:report_id>/generate')
class ReportGenerationResource(Resource):
    @jwt_required()
    def post(self, report_id):
        """Generate a report based on its configuration."""
        current_user = get_jwt_identity()
        data = request.json

        try:
            report = Report.query.filter_by(
                id=report_id,
                is_deleted=False
            ).first()
            if not report:
                return {'message': 'Report not found'}, 404

            has_access = report.has_access(
                current_user['id'],
                current_user.get('role_id')
            )
            if not has_access:
                return {'message': 'Unauthorized access'}, 403

            # Get report parameters
            filters = data.get('filters', report.parameters or {})
            aggregate_by = data.get('aggregate_by')
            output_format = data.get('format', 'csv')

            # Generate report based on type
            report_type = report.report_type
            if report_type == ReportType.SALES_PERFORMANCE.value:
                return self.generate_sales_report(
                    filters,
                    aggregate_by,
                    output_format
                )
            elif report_type == ReportType.PAYPOINT_PERFORMANCE.value:
                return self.generate_paypoint_report(
                    filters,
                    aggregate_by,
                    output_format
                )
            elif report_type == ReportType.PRODUCT_PERFORMANCE.value:
                return self.generate_product_report(
                    filters,
                    aggregate_by,
                    output_format
                )
            elif report_type == ReportType.CUSTOM.value:
                return self.generate_custom_report(
                    report,
                    filters,
                    output_format
                )
            else:
                return {'message': 'Unsupported report type'}, 400

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return {'message': 'Error generating report'}, 500

    def generate_sales_report(self, filters, aggregate_by, output_format):
        """Generate a sales performance report."""
        try:
            # Build and execute the query
            query = self.build_sales_query(filters)
            query = self.apply_filters(query, filters)

            # Get aggregation results if needed
            aggregation_results = {}
            if aggregate_by:
                aggregation_results = self.calculate_aggregates(
                    query,
                    aggregate_by
                )

            # Generate report in specified format
            if output_format == 'csv':
                return self.stream_csv_response(
                    query.all(),
                    aggregation_results
                )
            else:
                return {'message': 'Unsupported format'}, 400

        except Exception as e:
            error_msg = f"Error generating sales report: {str(e)}"
            logger.error(error_msg)
            return {'message': error_msg}, 500

    def generate_paypoint_report(self, filters, aggregate_by, output_format):
        """Generate a paypoint performance report."""
        try:
            # Similar implementation to sales report but focused on paypoint metrics
            pass
        except Exception as e:
            error_msg = f"Error generating paypoint report: {str(e)}"
            logger.error(error_msg)
            return {'message': error_msg}, 500

    def generate_product_report(self, filters, aggregate_by, output_format):
        """Generate a product performance report."""
        try:
            # Similar implementation to sales report but focused on product metrics
            pass
        except Exception as e:
            error_msg = f"Error generating product report: {str(e)}"
            logger.error(error_msg)
            return {'message': error_msg}, 500

    def generate_custom_report(self, report, filters, output_format):
        """Generate a custom report based on user-defined configuration."""
        try:
            # Get custom report configuration
            custom_report_id = report.parameters.get('custom_report_id')
            custom_report = CustomReport.query.filter_by(
                id=custom_report_id
            ).first()
            if not custom_report:
                return {
                    'message': 'Custom report configuration not found'
                }, 404

            # Generate report based on custom configuration
            pass
        except Exception as e:
            error_msg = f"Error generating custom report: {str(e)}"
            logger.error(error_msg)
            return {'message': error_msg}, 500

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
