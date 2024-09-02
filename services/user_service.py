from flask import Flask, redirect, url_for, session, request, jsonify
from flask_session import Session
from msal import ConfidentialClientApplication
from models.user_model import User
from models.audit_model import AuditTrail
from app import db
from datetime import datetime

class UserService:
    @staticmethod
    def create_user(data):
        new_user = User(
            email=data['email'],
            name=data['name'],
            role_id=data['role_id'],
            microsoft_id=data['microsoft_id']
        )
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @staticmethod
    def update_user(user_id, data):
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return None

        user.email = data.get('email', user.email)
        user.name = data.get('name', user.name)
        user.role_id = data.get('role_id', user.role_id)
        user.updated_at = datetime.utcnow()

        db.session.commit()
        return user

    @staticmethod
    def delete_user(user_id):
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return None

        user.is_deleted = True
        db.session.commit()
        return user
