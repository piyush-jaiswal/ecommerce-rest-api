from unittest.mock import patch

import pytest


class TestHealthCheck:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client

    def test_health_check_healthy(self):
        """Test health check endpoint when all components are healthy."""
        response = self.client.get("/health")

        assert response.status_code == 200
        assert response.content_type == "application/json"

        data = response.get_json()

        # Verify response structure
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data

        # Verify overall status
        assert data["status"] == "healthy"

        # Verify timestamp format (ISO 8601)
        timestamp = data["timestamp"]
        assert timestamp.endswith("Z") or "+" in timestamp or timestamp.endswith(":00")

        # Verify components
        components = data["components"]
        assert "database" in components
        assert "application" in components

        # Verify database component
        db_component = components["database"]
        assert db_component["status"] == "up"
        assert "response_time_ms" in db_component
        assert isinstance(db_component["response_time_ms"], (int, float))
        assert db_component["response_time_ms"] >= 0

        # Verify application component
        app_component = components["application"]
        assert app_component["status"] == "up"
        assert app_component["version"] == "v1"

    @patch("app.routes.health.db.engine.connect")
    def test_health_check_database_down(self, mock_connect):
        """Test health check when database is not accessible."""
        # Mock database connection failure
        mock_connect.side_effect = Exception("Connection refused")

        response = self.client.get("/health")
        assert response.status_code == 503
        data = response.get_json()

        # Verify overall status is unhealthy
        assert data["status"] == "unhealthy"

        # Verify database component shows error
        db_component = data["components"]["database"]
        assert db_component["status"] == "down"
        assert "error" in db_component
        assert db_component["error"] == "Database health check failed"
        assert db_component["response_time_ms"] is None

        # Verify application component is still up
        app_component = data["components"]["application"]
        assert app_component["status"] == "up"

    def test_health_check_response_timing(self):
        """Test that health check measures response times accurately."""
        response = self.client.get("/health")

        assert response.status_code == 200

        data = response.get_json()
        db_response_time = data["components"]["database"]["response_time_ms"]

        # Response time should be reasonable (less than 1000ms for in-memory SQLite)
        assert 0 <= db_response_time <= 1000

        # Response time should be a number with reasonable precision
        assert isinstance(db_response_time, (int, float))

    def test_health_check_endpoint_no_auth_required(self):
        """Test that health check endpoint doesn't require authentication."""
        # The health check should work without any authentication headers
        response = self.client.get("/health")
        assert response.status_code in [
            200,
            503,
        ]  # Either healthy or unhealthy, not 401

    def test_health_check_json_structure_consistency(self):
        """Test that the JSON response structure is consistent."""
        response = self.client.get("/health")
        data = response.get_json()

        # Required top-level keys
        required_keys = {"status", "timestamp", "components"}
        assert set(data.keys()) == required_keys

        # Required component keys
        required_components = {"database", "application"}
        assert set(data["components"].keys()) == required_components

        # Database component required keys (when healthy)
        if data["components"]["database"]["status"] == "up":
            db_required_keys = {"status", "response_time_ms"}
            assert set(data["components"]["database"].keys()) == db_required_keys

        # Application component required keys
        app_required_keys = {"status", "version"}
        assert set(data["components"]["application"].keys()) == app_required_keys

    def test_multiple_health_check_calls(self):
        """Test that multiple calls to health check return consistent results."""
        responses = []

        for _ in range(3):
            response = self.client.get("/health")
            responses.append(response)

        # All responses should have the same status code
        status_codes = [r.status_code for r in responses]
        assert len(set(status_codes)) == 1  # All status codes should be the same

        # All should return valid JSON
        for response in responses:
            data = response.get_json()
            assert "status" in data
            assert "components" in data
