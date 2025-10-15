from flask import Flask

from app.extensions import api, db, jwt, migrate
from config import DevelopmentConfig


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # initialize extenstions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)

    # register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.category import bp as category_bp
    from app.routes.product import bp as product_bp
    from app.routes.subcategory import bp as subcategory_bp

    api.register_blueprint(category_bp, url_prefix="/categories")
    api.register_blueprint(subcategory_bp, url_prefix="/subcategories")
    api.register_blueprint(product_bp, url_prefix="/products")
    api.register_blueprint(auth_bp, url_prefix="/auth")

    return app
