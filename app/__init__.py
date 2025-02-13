import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flasgger import Swagger
from sqlalchemy import MetaData


app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=3)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=3)

# PostgreSQL-compatible naming convention (to follow the naming convention already used in the DB)
# https://stackoverflow.com/questions/4107915/postgresql-default-constraint-names
naming_convention = {
    "ix": "%(table_name)s_%(column_0_name)s_idx",       # Indexes
    "uq": "%(table_name)s_%(column_0_name)s_key",       # Unique constraints
    "ck": "%(table_name)s_%(constraint_name)s_check",   # Check constraints
    "fk": "%(table_name)s_%(column_0_name)s_fkey",      # Foreign keys
    "pk": "%(table_name)s_pkey"                         # Primary keys
}
metadata = MetaData(naming_convention=naming_convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)
jwt = JWTManager(app)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    err = "Access token expired. Use your refresh token to get a new one."
    if jwt_payload['type'] == 'refresh':
        err = "Refresh token expired. Please login again."
    return jsonify(code="token_expired", error=err), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify(code="invalid_token", error="Invalid token provided."), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify(code="authorization_required", error="JWT needed for this operation. Login, if needed."), 401


from app import routes

swagger_config = {
    'openapi': '3.0.0',
    'title': 'Ecommerce REST API',
    'version': None,
    'termsOfService': None,
    'description': None,
    'specs': [
        {
            "endpoint": 'api_spec',
            "route": '/api_spec.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    'specs_route': '/',
}

template = {
    'tags': [
        {'name': 'Category', 'description': 'Operations with categories'},
        {'name': 'Subcategory', 'description': 'Operations with subategories'},
        {'name': 'Product', 'description': 'Operations with products'}
    ]
}
swagger = Swagger(app, template=template, config=swagger_config, merge=True)
