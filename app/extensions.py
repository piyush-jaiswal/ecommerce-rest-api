from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData


# PostgreSQL-compatible naming convention (to follow the naming convention already used in the DB)
# https://stackoverflow.com/questions/4107915/postgresql-default-constraint-names
naming_convention = {
    "ix": "%(table_name)s_%(column_0_name)s_idx",  # Indexes
    "uq": "%(table_name)s_%(column_0_name)s_key",  # Unique constraints
    "ck": "%(table_name)s_%(constraint_name)s_check",  # Check constraints
    "fk": "%(table_name)s_%(column_0_name)s_fkey",  # Foreign keys
    "pk": "%(table_name)s_pkey",  # Primary keys
}
metadata = MetaData(naming_convention=naming_convention)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate(db)
jwt = JWTManager()
api = Api()


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    err = "Access token expired. Use your refresh token to get a new one."
    if jwt_payload["type"] == "refresh":
        err = "Refresh token expired. Please login again."
    return jsonify(code="token_expired", error=err), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify(code="invalid_token", error="Invalid token provided."), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify(
        code="authorization_required",
        error="JWT needed for this operation. Login, if needed.",
    ), 401
