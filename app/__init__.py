import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flasgger import Swagger
from sqlalchemy import MetaData


app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
