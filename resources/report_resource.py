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
report_ns = Namespace('reports', description='Sales and Performance Report Generation')

# Define the model for Swagger documentation
report_model = report_ns.model('Report', {
    'report_type': fields.String(required=True, description='Type of the report to generate')
})

class ReportResource(Resource):
    MIN_DATA_DAYS = 60  # Minimum number of days of data required for meaningful analysis

    @report_ns.doc(security='Bearer Auth')
    @jwt_required()
    @report_ns.param('report_type', 'The type of report to generate')
    def get(self):
        """Generate and return a report with visualizations if requested."""
        current_user = get_jwt_identity()

        report_type = request.args.get('report_type', None)
        if not report_type:
            return {'message': 'Report type is required'}, 400

        # Route to the correct report generation function
        report_type = report_type.lower()
        if report_type == 'performance':
            return self.generate_performance_report()
        elif report_type == 'sales':
            return self.generate_sales_report()
        elif report_type == 'branch':
            return self.generate_branch_wise_report()
        elif report_type == 'sales_executive':
            return self.generate_sales_executive_wise_report()
        elif report_type == 'sales_manager':
            return self.generate_sales_manager_wise_report()
        elif report_type == 'predictive':
            return self.generate_predictive_report()
        elif report_type == 'lstm_predictive':
            return self.generate_lstm_predictive_report()
        else:
            return {'message': 'Invalid report type'}, 400

    def check_data_sufficiency(self, df):
        """Check if the dataset has enough data for analysis."""
        unique_dates = df['created_at'].nunique()
        if unique_dates < self.MIN_DATA_DAYS:
            return False, self.MIN_DATA_DAYS - unique_dates
        return True, 0

    def generate_performance_report(self):
        """Generate a performance report with visualizations."""
        sales_data = db.session.query(
            SalesExecutive.name, Branch.name, db.func.sum(Sale.amount).label('total_sales')
        ).join(Sale).join(Branch).group_by(SalesExecutive.name, Branch.name).all()

        df = pd.DataFrame(sales_data, columns=['Sales Executive', 'Branch', 'Total Sales'])

        # Check if there’s enough data
        sufficient_data, days_needed = self.check_data_sufficiency(df)
        if not sufficient_data:
            return {
                'message': f'Insufficient data. Please collect at least {days_needed} more days of data.',
                'status': 'insufficient_data'
            }, 200

        # Visualization: Bar plot for sales per branch
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Branch', y='Total Sales', data=df)
        plt.xticks(rotation=45)
        plt.title('Total Sales per Branch')
        plt.tight_layout()

        return self.export_visualization('performance_sales_barplot')

    def generate_sales_report(self):
        """Generate a sales report with visualizations."""
        sales_data = db.session.query(Sale).all()
        df = pd.DataFrame([sale.serialize() for sale in sales_data])

        if df.empty:
            return {'message': 'No sales data available'}, 200

        # Visualization: Line graph for sales over time
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)
        df['amount'].plot(figsize=(10, 6), title="Sales Over Time")
        plt.tight_layout()

        return self.export_visualization('sales_line_graph')

    def generate_branch_wise_report(self):
        """Generate a branch-wise report with visualizations."""
        sales_data = db.session.query(
            Branch.name, db.func.sum(Sale.amount).label('total_sales')
        ).join(Sale).group_by(Branch.name).all()

        df = pd.DataFrame(sales_data, columns=['Branch', 'Total Sales'])

        if df.empty:
            return {'message': 'No branch sales data available'}, 200

        # Visualization: Pie chart for sales distribution by branch
        plt.figure(figsize=(8, 8))
        df.set_index('Branch')['Total Sales'].plot.pie(autopct='%1.1f%%', startangle=90)
        plt.title('Sales Distribution by Branch')
        plt.ylabel('')
        plt.tight_layout()

        return self.export_visualization('branch_sales_pie_chart')

    def generate_sales_executive_wise_report(self):
        """Generate a sales executive-wise report."""
        sales_data = db.session.query(
            SalesExecutive.name, db.func.sum(Sale.amount).label('total_sales')
        ).join(Sale).group_by(SalesExecutive.name).all()

        df = pd.DataFrame(sales_data, columns=['Sales Executive', 'Total Sales'])

        if df.empty:
            return {'message': 'No sales executive data available'}, 200

        return self.export_to_format(df, 'sales_executive_wise_report')

    def generate_sales_manager_wise_report(self):
        """Generate a sales manager-wise report."""
        sales_data = db.session.query(
            User.name, db.func.sum(Sale.amount).label('total_sales')
        ).join(Sale).group_by(User.name).all()

        df = pd.DataFrame(sales_data, columns=['Sales Manager', 'Total Sales'])

        if df.empty:
            return {'message': 'No sales manager data available'}, 200

        return self.export_to_format(df, 'sales_manager_wise_report')

    def generate_predictive_report(self):
        """Generate a predictive sales report based on historical data using ARIMA."""
        sales_data = db.session.query(Sale).all()

        df = pd.DataFrame([sale.serialize() for sale in sales_data])
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)

        sufficient_data, days_needed = self.check_data_sufficiency(df)
        if not sufficient_data:
            return {
                'message': f'Insufficient data for prediction. Please collect at least {days_needed} more days of data.',
                'status': 'insufficient_data'
            }, 200

        # Train ARIMA model for time-series forecasting
        model = auto_arima(df['amount'], seasonal=False, stepwise=True, suppress_warnings=True)

        # Predict sales for the next 30 days
        forecast = model.predict(n_periods=30)
        forecast_dates = pd.date_range(start=datetime.today(), periods=30, freq='D')

        future_df = pd.DataFrame({
            'Date': forecast_dates,
            'Predicted Sales': forecast
        })

        # Visualization: Line plot for predictions
        plt.figure(figsize=(10, 6))
        plt.plot(future_df['Date'], future_df['Predicted Sales'], label='Predicted Sales')
        plt.title('Predicted Sales for the Next 30 Days')
        plt.xlabel('Date')
        plt.ylabel('Sales Amount')
        plt.legend()
        plt.tight_layout()

        return self.export_visualization('sales_forecast_line_plot')

    def generate_lstm_predictive_report(self):
        """Generate a predictive sales report using LSTM."""
        sales_data = db.session.query(Sale).all()

        df = pd.DataFrame([sale.serialize() for sale in sales_data])
        df['created_at'] = pd.to_datetime(df['created_at'])
        df.set_index('created_at', inplace=True)

        sufficient_data, days_needed = self.check_data_sufficiency(df)
        if not sufficient_data:
            return {
                'message': f'Insufficient data for LSTM prediction. Please collect at least {days_needed} more days of data.',
                'status': 'insufficient_data'
            }, 200

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

        for i in range(len(df)):
            row = df.iloc[i].to_string()
            pdf.cell(200, 10, txt=row, ln=True)

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
            'performance': self.generate_performance_report,
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
