from flask_restful import Resource
from models.report_model import Report
from models.audit_model import AuditTrail
from flask import request, jsonify
from app import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

class ReportResource(Resource):
    @jwt_required()
    def get(self, report_id=None):
        current_user = get_jwt_identity()
        if report_id:
            report = Report.query.filter_by(id=report_id).first()
            if not report:
                return {'message': 'Report not found'}, 404

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='report',
                resource_id=report_id,
                details=f"User accessed report with ID {report_id}"
            )
            db.session.add(audit)
            db.session.commit()

            return report.serialize(), 200
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            filter_by = request.args.get('filter_by', None)
            sort_by = request.args.get('sort_by', 'created_at')

            reports_query = Report.query

            if filter_by:
                reports_query = reports_query.filter(Report.report_data.ilike(f'%{filter_by}%'))

            reports = reports_query.order_by(sort_by).paginate(page, per_page, error_out=False)

            # Log the access to audit trail
            audit = AuditTrail(
                user_id=current_user['id'],
                action='ACCESS',
                resource_type='report',
                resource_id=None,
                details=f"User accessed list of reports"
            )
            db.session.add(audit)
            db.session.commit()

            return {
                'reports': [report.serialize() for report in reports.items],
                'total': reports.total,
                'pages': reports.pages,
                'current_page': reports.page
            }, 200

    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data = request.json

        # Validate that report_data is present
        if 'report_data' not in data:
            return {'message': 'Missing required field: report_data'}, 400

        new_report = Report(
            user_id=current_user['id'],
            report_data=data['report_data']
        )
        db.session.add(new_report)
        db.session.commit()

        # Log the creation to audit trail
        audit = AuditTrail(
            user_id=current_user['id'],
            action='CREATE',
            resource_type='report',
            resource_id=new_report.id,
            details=f"User created a new report with ID {new_report.id}"
        )
        db.session.add(audit)
        db.session.commit()

        return new_report.serialize(), 201
