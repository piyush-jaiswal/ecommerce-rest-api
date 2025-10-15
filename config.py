import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    # sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # jwt
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=3)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=3)

    # flask-smorest
    API_TITLE = "Ecommerce REST API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.2"

    # flask-smorest openapi swagger
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # flask-smorest Swagger UI top level authorize dialog box
    API_SPEC_OPTIONS = {
        "components": {
            "securitySchemes": {
                "access_token": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter your JWT access token",
                },
                "refresh_token": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter your JWT refresh token",
                },
            }
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = os.urandom(24).hex()


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
