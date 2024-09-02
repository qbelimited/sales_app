from flask import Flask, redirect, url_for, session, request, jsonify
from flask_session import Session
from msal import ConfidentialClientApplication
from models.user_model import User
from models.audit_model import AuditTrail
from models.sales_model import Sale
from app import db
from datetime import datetime

class SalesService:
    @staticmethod
    def create_sale(data, current_user_id):
        new_sale = Sale(
            user_id=current_user_id,
            sale_manager=data['sale_manager'],
            sales_executive_id=data['sales_executive_id'],
            branch_id=data['branch_id'],
            client_phone=data['client_phone'],
            bank_name=data.get('bank_name'),
            bank_branch=data.get('bank_branch'),
            bank_acc_number=data.get('bank_acc_number'),
            amount=data['amount'],
            geolocation=data.get('geolocation')
        )
        db.session.add(new_sale)
        db.session.commit()
        return new_sale

    @staticmethod
    def update_sale(sale_id, data):
        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return None

        sale.sale_manager = data.get('sale_manager', sale.sale_manager)
        sale.sales_executive_id = data.get('sales_executive_id', sale.sales_executive_id)
        sale.branch_id = data.get('branch_id', sale.branch_id)
        sale.client_phone = data.get('client_phone', sale.client_phone)
        sale.bank_name = data.get('bank_name', sale.bank_name)
        sale.bank_branch = data.get('bank_branch', sale.bank_branch)
        sale.bank_acc_number = data.get('bank_acc_number', sale.bank_acc_number)
        sale.amount = data.get('amount', sale.amount)
        sale.updated_at = datetime.utcnow()

        db.session.commit()
        return sale

    @staticmethod
    def delete_sale(sale_id):
        sale = Sale.query.filter_by(id=sale_id, is_deleted=False).first()
        if not sale:
            return None

        sale.is_deleted = True
        db.session.commit()
        return sale
