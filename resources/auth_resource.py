from flask_restful import Resource
from flask import request, session
from services.auth_service import AuthService

auth_service = AuthService()

class AuthResource(Resource):
    def get(self):
        return auth_service.login()

class AuthCallbackResource(Resource):
    def get(self):
        return auth_service.handle_callback(request.args)

class LogoutResource(Resource):
    def get(self):
        session.clear()
        return {"message": "Logged out successfully"}
