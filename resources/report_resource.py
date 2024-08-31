from flask_restful import Resource
from models.report_model import Report
from flask import request, jsonify
from app import db

class ReportResource(Resource):
    def get(self, report_id=None):
        if report_id:
            report = Report.query.get(report_id)
            if not report:
                return {'message': 'Report not found'}, 404
            return report.serialize(), 200
        else:
            reports = Report.query.all()
            return jsonify([report.serialize() for report in reports])

    def post(self):
        data = request.json
        new_report = Report(
            user_id=data['user_id'],
            report_data=data['report_data']
        )
        db.session.add(new_report)
        db.session.commit()
        return new_report.serialize(), 201
