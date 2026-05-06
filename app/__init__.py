import logging

from flask import Flask

from app.extensions import api, db, jwt, migrate
from app.middleware.request_logger import RequestLogger
from config import config


def _setup_sentry(dsn, env="production"):
    import sentry_sdk

    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=False,
        include_source_context=False,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=0.2,
        # To collect profiles for all profile sessions,
        # set `profile_session_sample_rate` to 1.0.
        profile_session_sample_rate=0.2,
        # Profiles will be automatically collected while
        # there is an active span.
        profile_lifecycle="trace",
        # Enable logs to be sent to Sentry
        enable_logs=True,
    )


def _configure_logging(env):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if env in ("preview", "production"):
        sentry_dsn = getattr(config[env], "SENTRY_DSN", None)
        if not sentry_dsn:
            logging.warning("Could not setup sentry. SENTRY_DSN not found.")
            return

        _setup_sentry(sentry_dsn, env)
        logging.info(f"Sentry initialized for {env}")


def create_app(env="development", **kwargs):
    # Use app.logger for logging
    _configure_logging(env)

    app = Flask(__name__)
    app.config.from_object(config[env](**kwargs))
    app.url_map.strict_slashes = False

    if app.config.get("LOG_REQUESTS"):
        RequestLogger(app)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    api.init_app(app)

    # register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.category import bp as category_bp
    from app.routes.health import bp as health_bp
    from app.routes.product import bp as product_bp
    from app.routes.subcategory import bp as subcategory_bp

    # register with app to exclude from openapi
    app.register_blueprint(health_bp)

    api.register_blueprint(category_bp, url_prefix="/categories")
    api.register_blueprint(subcategory_bp, url_prefix="/subcategories")
    api.register_blueprint(product_bp, url_prefix="/products")
    api.register_blueprint(auth_bp, url_prefix="/auth")

    return app
