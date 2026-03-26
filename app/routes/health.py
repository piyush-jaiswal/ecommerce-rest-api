import time
from datetime import datetime, timezone

from flask import current_app, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import text

from app import db

bp = Blueprint("Health", __name__)


@bp.route("/health")
class HealthCheck(MethodView):
    init_every_request = False

    def get(self):
        timestamp = datetime.now(timezone.utc).isoformat()
        components = {}
        overall_status = "healthy"

        # Test database connectivity
        try:
            db_start_time = time.time()
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            db_response_time = round((time.time() - db_start_time) * 1000, 2)

            components["database"] = {
                "status": "up",
                "response_time_ms": db_response_time,
            }
        except Exception as e:
            current_app.logger.error(f"Database health check failed: {e}")
            components["database"] = {
                "status": "down",
                "error": "Database health check failed",
                "response_time_ms": None,
            }
            overall_status = "unhealthy"

        # Add application info
        components["application"] = {
            "status": "up",
            "version": "v1",  # Matches API_VERSION from config
        }

        response_data = {
            "status": overall_status,
            "timestamp": timestamp,
            "components": components,
        }

        # Return appropriate HTTP status code
        status_code = 200 if overall_status == "healthy" else 503
        return jsonify(response_data), status_code
