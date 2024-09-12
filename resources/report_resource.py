import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from flask_restx import Namespace, Resource, fields
from flask import request, jsonify, send_file
from models.sales_model import Sale
from models.sales_executive_model import SalesExecutive
from models.branch_model import Branch
from models.user_model import User
from models.audit_model import AuditTrail
from models.paypoint_model import Paypoint
from models.bank_model import Bank, BankBranch
from models.inception_model import Inception
from models.under_investigation_model import UnderInvestigation
from models.query_model import Query
from models.performance_model import SalesTarget
from pmdarima import auto_arima
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from joblib import Parallel, delayed
from sqlalchemy import or_
from fpdf import FPDF

# Define namespace for report-related operations
report_ns = Namespace('reports', description='Comprehensive Sales and Performance Report Generation')

# Define the model for Swagger documentation
report_model = report_ns.model('Report', {
    'report_type': fields.String(required=True, description='Type of the report to generate'),
    'filters': fields.Raw(description="Filters for the report"),
    'group_by': fields.String(description="Group by field for data aggregation")
})

class ComprehensiveReportResource(Resource):

    @report_ns.doc(security='Bearer Auth')
    @jwt_required()
    @report_ns.expect(report_model, validate=True)
    def post(self):
        """Generate a comprehensive dynamic report with filters, statistics, and visualizations."""
        current_user = get_jwt_identity()
        data = request.json
        report_type = data.get('report_type')
        filters = data.get('filters', {})
        group_by = data.get('group_by', None)

        # Step 1: Fetch and combine data from different models
        combined_df = self.fetch_combined_data(filters)

        # Step 2: Apply filtering logic
        if filters:
            combined_df = self.apply_filters(combined_df, filters)

        # Step 3: Handle different report types
        if report_type == 'sales_performance':
            return self.generate_sales_performance_report(combined_df, group_by)
        elif report_type == 'investigations':
            return self.generate_investigations_report(combined_df, group_by)
        elif report_type == 'queries':
            return self.generate_queries_report(combined_df, group_by)
        elif report_type == 'statistics':
            return self.generate_statistics_report(combined_df)
        elif report_type == 'predictive':
            return self.generate_predictive_report(combined_df)
        elif report_type == 'lstm_predictive':
            return self.generate_lstm_predictive_report(combined_df)
        else:
            return {'message': 'Invalid report type'}, 400

    def fetch_combined_data(self, filters):
        """Fetch sales data combined with Inception, Paypoint, Bank, Sales Executive, Investigations, Queries."""
        sales_data = db.session.query(Sale).all()
        sales_df = pd.DataFrame([sale.serialize() for sale in sales_data])

        # Fetch additional data and merge into sales_df
        inception_data = db.session.query(Inception).all()
        inception_df = pd.DataFrame([inception.serialize() for inception in inception_data])

        paypoint_data = db.session.query(Paypoint).all()
        paypoint_df = pd.DataFrame([paypoint.serialize() for paypoint in paypoint_data])

        bank_data = db.session.query(Bank).all()
        bank_df = pd.DataFrame([bank.serialize() for bank in bank_data])

        branch_data = db.session.query(BankBranch).all()
        branch_df = pd.DataFrame([branch.serialize() for branch in branch_data])

        sales_executive_data = db.session.query(SalesExecutive).all()
        sales_executive_df = pd.DataFrame([se.serialize() for se in sales_executive_data])

        product_data = db.session.query(ImpactProduct).all()
        product_df = pd.DataFrame([product.serialize() for product in product_data])

        investigation_data = db.session.query(UnderInvestigation).all()
        investigation_df = pd.DataFrame([inv.serialize() for inv in investigation_data])

        query_data = db.session.query(Query).all()
        query_df = pd.DataFrame([q.serialize() for q in query_data])

        # Merge all the data into a single DataFrame
        merged_df = pd.merge(sales_df, inception_df, how='left', on='sale_id')
        merged_df = pd.merge(merged_df, paypoint_df, how='left', on='paypoint_id')
        merged_df = pd.merge(merged_df, bank_df, how='left', on='bank_id')
        merged_df = pd.merge(merged_df, branch_df, how='left', on='bank_branch_id')
        merged_df = pd.merge(merged_df, sales_executive_df, how='left', on='sales_executive_id')
        merged_df = pd.merge(merged_df, product_df, how='left', on='policy_type_id')
        merged_df = pd.merge(merged_df, investigation_df, how='left', on='sale_id')
        merged_df = pd.merge(merged_df, query_df, how='left', on='sale_id')

        return merged_df

    def apply_filters(self, df, filters):
        """Apply filters to the DataFrame."""
        for column, value in filters.items():
            if value:
                df = df[df[column] == value]
        return df

    def generate_sales_performance_report(self, df, group_by=None):
        """Generate sales performance report comparing sales against targets."""
        df['performance'] = (df['amount'] / df['target_amount']) * 100
        performance_df = df.groupby(group_by).agg({
            'amount': ['sum', 'min', 'max', 'mean'],
            'target_amount': ['sum', 'min', 'max', 'mean'],
            'performance': ['mean']
        })

        return self.export_to_format(performance_df, 'sales_performance_report')

    def generate_investigations_report(self, df, group_by=None):
        """Generate report on sales under investigation."""
        investigation_df = df[df['resolved'] == False].groupby(group_by).agg({
            'amount': ['sum', 'count'],
            'inception_amount': ['sum', 'count'],
        })

        return self.export_to_format(investigation_df, 'investigations_report')

    def generate_queries_report(self, df, group_by=None):
        """Generate report on sales queries and responses."""
        query_df = df.groupby(group_by).agg({
            'amount': ['sum', 'count'],
            'query_status': ['count'],  # Count of queried sales
            'response_status': ['count']  # Count of resolved queries
        })

        return self.export_to_format(query_df, 'queries_report')

    def generate_statistics_report(self, df):
        """Generate statistical report on sales and incepted amounts."""
        stats_sales = df['amount'].agg(['sum', 'min', 'max', 'mean', 'std', 'var']).to_dict()
        stats_incepted = df['inception_amount'].agg(['sum', 'min', 'max', 'mean', 'std', 'var']).to_dict()

        return {
            'sales_statistics': stats_sales,
            'inception_statistics': stats_incepted,
        }

    def generate_predictive_report(self, df):
        """Generate predictive sales report using ARIMA."""
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)

        # Ensure sufficient data
        if df.shape[0] < 60:  # Example condition for minimal data sufficiency
            return {'message': 'Insufficient data for prediction'}, 400

        # Train ARIMA model
        model = auto_arima(df['amount'], seasonal=False, stepwise=True, suppress_warnings=True)
        forecast = model.predict(n_periods=30)
        forecast_dates = pd.date_range(start=datetime.today(), periods=30, freq='D')

        # Generate forecast DataFrame
        future_df = pd.DataFrame({
            'Date': forecast_dates,
            'Predicted Sales': forecast
        })

        # Visualization: Line plot for predictions
        plt.plot(future_df['Date'], future_df['Predicted Sales'], label='Predicted Sales')
        plt.title('Predicted Sales for the Next 30 Days')
        plt.xlabel('Date')
        plt.ylabel('Sales Amount')
        plt.legend()
        plt.tight_layout()

        return self.export_visualization('predictive_sales_report')

    def generate_lstm_predictive_report(self, df):
        """Generate a predictive sales report using LSTM."""
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)

        # Ensure sufficient data
        if df.shape[0] < 60:  # Example condition for minimal data sufficiency
            return {'message': 'Insufficient data for LSTM prediction'}, 400

        # Normalize data
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df[['amount']])

        look_back = request.args.get('look_back', default=30, type=int)
        batch_size = request.args.get('batch_size', default=32, type=int)
        epochs = request.args.get('epochs', default=10, type=int)

        def create_dataset(data, look_back=1):
            X, y = [], []
            for i in range(len(data) - look_back - 1):
                X.append(data[i:(i + look_back), 0])
                y.append(data[i + look_back, 0])
            return np.array(X), np.array(y)

        X, y = create_dataset(scaled_data, look_back)
        X = np.reshape(X, (X.shape[0], X.shape[1], 1))

        model = Sequential()
        model.add(LSTM(50, return_sequences=True, input_shape=(look_back, 1)))
        model.add(LSTM(50))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mean_squared_error')

        model.fit(X, y, epochs=epochs, batch_size=batch_size)

        last_data = scaled_data[-look_back:]
        last_data = np.reshape(last_data, (1, look_back, 1))
        predicted_sales = model.predict(last_data)
        predicted_sales = scaler.inverse_transform(predicted_sales)

        future_df = pd.DataFrame({
            'Date': pd.date_range(start=datetime.today(), periods=30, freq='D'),
            'Predicted Sales': predicted_sales.flatten()
        })

        # Visualization: Line plot for predictions
        plt.figure(figsize=(10, 6))
        plt.plot(future_df['Date'], future_df['Predicted Sales'], label='Predicted Sales')
        plt.title('LSTM Predicted Sales for the Next 30 Days')
        plt.xlabel('Date')
        plt.ylabel('Sales Amount')
        plt.legend()
        plt.tight_layout()

        return self.export_visualization('lstm_sales_forecast')

    def export_to_format(self, df, filename):
        """Export DataFrame to the desired format (Excel or PDF)."""
        export_format = request.args.get('format', 'excel').lower()

        if export_format == 'pdf':
            return self.export_to_pdf(df, filename)
        else:
            return self.export_to_excel(df, filename)

    def export_visualization(self, filename):
        """Export the visualization as a PNG image."""
        output = BytesIO()
        plt.savefig(output, format='png')
        output.seek(0)
        plt.close()
        return send_file(output, attachment_filename=f"{filename}.png", as_attachment=True)

    def export_to_excel(self, df, filename):
        """Export the DataFrame to an Excel file."""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
            writer.save()

        output.seek(0)
        return send_file(output, attachment_filename=f"{filename}.xlsx", as_attachment=True)

    def export_to_pdf(self, df, filename):
        """Export the DataFrame to a PDF file."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for row in df.to_dict(orient='records'):
            row_text = ', '.join(f"{key}: {value}" for key, value in row.items())
            pdf.cell(200, 10, txt=row_text, ln=True)

        output = BytesIO()
        pdf.output(output)
        output.seek(0)
        return send_file(output, attachment_filename=f"{filename}.pdf", as_attachment=True)


# Register ParallelReportResource if needed
class ParallelReportResource(Resource):
    @jwt_required()
    def get(self):
        """Generate reports in parallel using joblib."""

        # Use joblib to parallelize report generation tasks
        reports = ['performance', 'sales', 'branch', 'sales_executive', 'sales_manager']
        parallel_reports = Parallel(n_jobs=-1)(delayed(self.generate_report)(report) for report in reports)

        return jsonify({
            'message': 'Reports generated successfully in parallel',
            'report_paths': parallel_reports
        })

    def generate_report(self, report_type):
        """Generate report based on report type."""
        report_mapping = {
            'performance': self.generate_sales_performance_report,
            'sales': self.generate_sales_report,
            'branch': self.generate_branch_wise_report,
            'sales_executive': self.generate_sales_executive_wise_report,
            'sales_manager': self.generate_sales_manager_wise_report,
            'predictive': self.generate_predictive_report,
            'lstm_predictive': self.generate_lstm_predictive_report
        }

        if report_type in report_mapping:
            return report_mapping[report_type]()
        else:
            return {'message': 'Invalid report type'}, 400
