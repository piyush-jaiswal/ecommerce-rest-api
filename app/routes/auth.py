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

bp = Blueprint("Auth", __name__)


@bp.route("/register")
class Register(MethodView):
    @bp.doc(summary="Register a new user")
    @bp.arguments(AuthIn)
    @bp.response(201)
    def post(self, data):
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
    @bp.doc(summary="Login a user")
    @bp.arguments(AuthIn)
    @bp.response(200, AuthOut)
    def post(self, data):
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
    @jwt_required(refresh=True)
    @bp.doc(
        summary="Get new access token using your refresh token",
        security=[{"refresh_token": []}],
    )
    @bp.response(200, AuthOut(only=("access_token",)))
    def post(self):
        identity = get_jwt_identity()
        return {"access_token": create_access_token(identity=identity, fresh=False)}
