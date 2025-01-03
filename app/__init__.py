import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flasgger import Swagger


app = Flask(__name__)

load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
            'tags': [
                {'name': 'Category', 'description': 'Operations with categories'},
                {'name': 'Subategory', 'description': 'Operations with subategories'},
                {'name': 'Product', 'description': 'Operations with products'}
            ],
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
