from email_validator import EmailNotValidError
from flask import jsonify, make_response
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User
from app.schemas import AuthIn, AuthOut

bp = Blueprint("auth", __name__)


@bp.route("/register")
class Register(MethodView):
    @bp.arguments(AuthIn)
    @bp.response(201)
    def post(self, data):
        """
        Register a new user.
        ---
        tags:
            - User
        description: Register a new user.
        requestBody:
            required: true
            description: email - Email id <br> password - Password
            content:
                application/json:
                    schema:
                        type: object
                        required:
                            - email
                            - password
                        properties:
                            email:
                                type: string
                            password:
                                type: string
        responses:
            201:
                description: User registered successfully.
            400:
                description: Invalid input.
            409:
                description: Email already exists.
            500:
                description: Internal Server Error.
        """

        user = User()
        user.set_password(data["password"])

        try:
            user.set_email(data["email"])
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(make_response(jsonify(error="Email already exists"), 409))
        except EmailNotValidError as e:
            abort(
                make_response(jsonify(code="invalid_email_format", error=str(e)), 422)
            )

        return {"message": "Registered!"}


@bp.route("/login")
class Login(MethodView):
    """Login a user and return access & refresh tokens."""

    @bp.arguments(AuthIn)
    @bp.response(200, AuthOut)
    def post(self, data):
        """
        Login a user.
        ---
        tags:
            - User
        description: Login a user.
        requestBody:
            required: true
            description: email - Email id <br> password - Password
            content:
                application/json:
                    schema:
                        type: object
                        required:
                            - email
                            - password
                        properties:
                            email:
                                type: string
                            password:
                                type: string
        responses:
            200:
                description: User logged in successfully.
            400:
                description: Invalid input.
            401:
                description: Invalid email or password.
            500:
                description: Internal Server Error.
        """
        user = User.get(email=data["email"])
        if not user or not user.check_password(data["password"]):
            return abort(
                make_response(
                    jsonify(
                        error="Invalid email or password. Check again or register."
                    ),
                    401,
                )
            )

        return {
            "access_token": create_access_token(identity=str(user.id), fresh=True),
            "refresh_token": create_refresh_token(identity=str(user.id)),
        }


@bp.route("/refresh")
class Refresh(MethodView):
    """Get new access token using your refresh token."""

    @jwt_required(refresh=True)
    @bp.response(200, AuthOut(only=("access_token",)))
    def post(self):
        """
        Get new access token using your refresh token
        ---
        tags:
            - User
        description: Get new access token using your refresh token.
        security:
            - refresh_token: []
        responses:
            200:
                description: New access token.
            401:
                description: Token expired, missing or invalid.
            500:
                description: Internal Server Error.
        """
        identity = get_jwt_identity()
        return {"access_token": create_access_token(identity=identity, fresh=False)}
