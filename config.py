import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    # sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostgreSQL options
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_timeout": 30,  # Timeout when getting connection from pool
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_pre_ping": True,  # Verify connections before use
        "connect_args": {
            "connect_timeout": 30,  # Max 30s to establish connection
        },
    }

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

    # logging
    LOG_REQUESTS = False

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
    JWT_SECRET_KEY = os.urandom(24).hex()
    LOG_REQUESTS = True

    def __init__(self, **kwargs):
        super().__init__()
        TestingConfig.SQLALCHEMY_DATABASE_URI = kwargs["SQLALCHEMY_DATABASE_URI"]


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    LOG_REQUESTS = True


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "preview": ProductionConfig,
}
