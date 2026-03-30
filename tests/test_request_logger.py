import json
from unittest.mock import MagicMock, patch

import pytest
from flask import g

from app.middleware.request_logger import DataScrubber, RequestLogger


class TestDataScrubber:
    """Test the DataScrubber utility class for sensitive data redaction."""

    def test_scrub_query_string_with_sensitive_data(self):
        """Test that sensitive data in query strings is redacted."""
        mock_request = MagicMock()
        mock_request.query_string = b"username=john&password=secret123&token=abc123"

        result = DataScrubber.scrub_query_string(mock_request)
        data = json.loads(result)

        assert data["username"] == ["john"]
        assert data["password"] == ["[redacted]"]
        assert data["token"] == ["[redacted]"]

    def test_scrub_query_string_empty(self):
        """Test scrubbing empty query string."""
        mock_request = MagicMock()
        mock_request.query_string = b""

        result = DataScrubber.scrub_query_string(mock_request)
        assert result == ""

    def test_scrub_query_string_no_sensitive_data(self):
        """Test scrubbing query string with no sensitive data."""
        mock_request = MagicMock()
        mock_request.query_string = b"page=1&limit=10&category=electronics"

        result = DataScrubber.scrub_query_string(mock_request)
        data = json.loads(result)

        assert data["page"] == ["1"]
        assert data["limit"] == ["10"]
        assert data["category"] == ["electronics"]

    def test_scrub_query_string_case_insensitive(self):
        """Test that sensitive key matching is case insensitive."""
        mock_request = MagicMock()
        mock_request.query_string = b"Password=secret&API_KEY=key123&Secret=value"

        result = DataScrubber.scrub_query_string(mock_request)
        data = json.loads(result)

        assert data["Password"] == ["[redacted]"]
        assert data["API_KEY"] == ["[redacted]"]
        assert data["Secret"] == ["[redacted]"]

    def test_scrub_body_json_with_sensitive_data(self):
        """Test scrubbing JSON body with sensitive data."""
        mock_request = MagicMock()
        mock_request.get_data.return_value = (
            '{"username": "john", "password": "secret123", "email": "john@example.com"}'
        )
        mock_request.content_type = "application/json"

        result = DataScrubber.scrub_body(mock_request)
        data = json.loads(result)

        assert data["username"] == "john"
        assert data["password"] == "[redacted]"
        assert data["email"] == "john@example.com"

    def test_scrub_body_empty(self):
        """Test scrubbing empty body."""
        mock_request = MagicMock()
        mock_request.get_data.return_value = ""

        result = DataScrubber.scrub_body(mock_request)
        assert result == ""

    def test_scrub_body_invalid_json(self):
        """Test scrubbing invalid JSON body."""
        mock_request = MagicMock()
        mock_request.get_data.return_value = '{"invalid": json}'
        mock_request.content_type = "application/json"

        result = DataScrubber.scrub_body(mock_request)
        assert result == "<invalid json>"

    def test_scrub_body_form_data_with_sensitive_data(self):
        """Test scrubbing form-encoded data with sensitive data."""
        mock_request = MagicMock()
        mock_request.get_data.return_value = (
            "username=john&password=secret123&remember=true"
        )
        mock_request.content_type = "application/x-www-form-urlencoded"

        result = DataScrubber.scrub_body(mock_request)
        data = json.loads(result)

        assert data["username"] == ["john"]
        assert data["password"] == ["[redacted]"]
        assert data["remember"] == ["true"]

    def test_scrub_body_unsupported_content_type(self):
        """Test scrubbing unsupported content type."""
        mock_request = MagicMock()
        mock_request.get_data.return_value = "some binary data"
        mock_request.content_type = "application/octet-stream"

        result = DataScrubber.scrub_body(mock_request)
        assert result == "<unsupported format>"

    def test_scrub_body_unreadable_data(self):
        """Test handling unreadable request data."""
        mock_request = MagicMock()
        mock_request.get_data.side_effect = Exception("Cannot read data")

        result = DataScrubber.scrub_body(mock_request)
        assert result == "<unreadable>"

    def test_scrub_body_truncated_large_data(self):
        """Test truncation of large request bodies."""
        mock_request = MagicMock()
        large_data = '{"data": "' + "x" * 5000 + '"}'  # Larger than _MAX_BYTES (4096)
        mock_request.get_data.return_value = large_data
        mock_request.content_type = "application/json"

        result = DataScrubber.scrub_body(mock_request)
        assert result.endswith(" … [truncated]")
        assert len(result) < len(large_data)

    def test_scrub_json_nested_sensitive_data(self):
        """Test scrubbing nested JSON with sensitive data."""
        data = {
            "user": {
                "username": "john",
                "credentials": {"password": "secret123", "api_key": "key123"},
            },
            "settings": {"theme": "dark"},
        }

        result = DataScrubber._scrub_json(data)

        assert result["user"]["username"] == "john"
        assert result["user"]["credentials"]["password"] == "[redacted]"
        assert result["user"]["credentials"]["api_key"] == "[redacted]"
        assert result["settings"]["theme"] == "dark"

    def test_scrub_json_with_arrays(self):
        """Test scrubbing JSON with arrays containing sensitive data."""
        data = {
            "users": [
                {"username": "john", "password": "secret1"},
                {"username": "jane", "password": "secret2"},
            ]
        }

        result = DataScrubber._scrub_json(data)

        assert result["users"][0]["username"] == "john"
        assert result["users"][0]["password"] == "[redacted]"
        assert result["users"][1]["username"] == "jane"
        assert result["users"][1]["password"] == "[redacted]"

    def test_scrub_json_deeply_nested(self):
        """Test handling deeply nested JSON (depth limit)."""
        # Create deeply nested structure beyond the limit
        nested_data = {"level": 1}
        current = nested_data
        for i in range(25):  # Exceed the depth limit of 20
            current["nested"] = {"level": i + 2}
            current = current["nested"]

        result = DataScrubber._scrub_json(nested_data)

        # Navigate to the depth limit and verify truncation
        current_result = result
        for i in range(19):  # Navigate to near the limit
            current_result = current_result["nested"]

        assert current_result["nested"] == "<too deeply nested>"


class TestRequestLogger:
    """Test the RequestLogger middleware for request/response logging."""

    @pytest.fixture(autouse=True)
    def setup(self, app, client):
        """Set up test environment with Flask app and client."""
        self.app = app
        self.client = client
        # Initialize RequestLogger with the test app
        self.logger = RequestLogger(app)

    @patch.object(RequestLogger, "_duration_ms", return_value=123.45)
    def test_successful_request_logging(self, mock_duration, app):
        """Test logging of successful requests."""
        with patch.object(app.logger, "info") as mock_info:
            self.client.get("/health")

            # Verify info logging was called
            assert mock_info.called
            call_args = mock_info.call_args
            message, extra = call_args[0][0], call_args[1]["extra"]

            # Verify log message format
            assert "[localhost]" in message
            assert "GET /health ->" in message
            assert "200" in message
            assert "(123.45ms)" in message

            # Verify extra fields
            assert extra["http.method"] == "GET"
            assert extra["http.host"] == "localhost"
            assert extra["http.path"] == "/health"
            assert extra["http.status_code"] == 200
            assert extra["http.duration_ms"] == 123.45

    @patch.object(RequestLogger, "_duration_ms", return_value=67.89)
    def test_client_error_logging(self, mock_duration, app):
        """Test logging of 4xx client error responses."""
        with patch.object(app.logger, "warning") as mock_warning:
            self.client.get("/nonexistent")

            # Verify warning logging was called for 404
            assert mock_warning.called
            call_args = mock_warning.call_args
            message, extra = call_args[0][0], call_args[1]["extra"]

            # Verify log message format for error
            assert "[localhost]" in message
            assert "GET /nonexistent ->" in message
            assert "404" in message
            assert "(67.89ms)" in message

            # Verify extra fields for error
            assert extra["http.status_code"] == 404
            assert extra["http.duration_ms"] == 67.89

    def test_post_request_with_body_logging(self, app):
        """Test logging of POST requests with request body."""
        # POST to /health returns 405 (Method Not Allowed), so it logs as warning
        with patch.object(app.logger, "warning") as mock_warning:
            self.client.post(
                "/health",
                json={"username": "john", "password": "secret123"},
                content_type="application/json",
            )

            assert mock_warning.called
            call_args = mock_warning.call_args
            extra = call_args[1]["extra"]

            # Verify request body is scrubbed
            body_data = json.loads(extra["http.request.body"])
            assert body_data["username"] == "john"
            assert body_data["password"] == "[redacted]"

    def test_request_with_query_params_logging(self, app):
        """Test logging of requests with query parameters."""
        with patch.object(app.logger, "info") as mock_info:
            self.client.get("/health?page=1&token=secret123")

            assert mock_info.called
            call_args = mock_info.call_args
            extra = call_args[1]["extra"]

            # Verify query string is scrubbed
            query_data = json.loads(extra["http.query_string"])
            assert query_data["page"] == ["1"]
            assert query_data["token"] == ["[redacted]"]

    def test_before_request_sets_timing(self, app):
        """Test that before_request sets up timing variables."""
        with app.test_request_context("/test"):
            self.logger._before_request()

            # Verify timing variables are set
            assert hasattr(g, "log_start_time")
            assert hasattr(g, "log_emitted")
            assert g.log_emitted is False

    @patch("app.middleware.request_logger.time.perf_counter")
    def test_duration_calculation(self, mock_perf_counter, app):
        """Test duration calculation accuracy."""
        with app.test_request_context("/test"):
            g.log_start_time = 100.0
            mock_perf_counter.return_value = 100.123
            duration = RequestLogger._duration_ms()

            assert duration == 123.0  # (100.123 - 100.0) * 1000 rounded to 2 places

    @patch.object(RequestLogger, "_duration_ms", return_value=999.99)
    def test_teardown_request_on_exception(self, mock_duration, app):
        """Test that teardown_request logs unhandled exceptions."""
        with app.test_request_context("/test"):
            g.log_start_time = 100.0
            g.log_emitted = False  # Simulate exception bypassed after_request

            exception = ValueError("Test exception")

            with patch.object(app.logger, "error") as mock_error:
                self.logger._teardown_request(exception)

                # Verify error logging was called
                assert mock_error.called
                call_args = mock_error.call_args
                message, extra = call_args[0][0], call_args[1]["extra"]

                # Verify error log message format
                assert "[localhost]" in message
                assert "GET /test -> 500" in message
                assert "(999.99ms)" in message

                # Verify error-specific extra fields
                assert extra["http.status_code"] == 500
                assert extra["error.type"] == "ValueError"
                assert extra["error.message"] == "Test exception"
                assert mock_error.call_args[1]["exc_info"] is True

    def test_teardown_request_no_exception(self, app):
        """Test that teardown_request does nothing when no exception occurred."""
        with app.test_request_context("/test"):
            with patch.object(app.logger, "error") as mock_error:
                self.logger._teardown_request(None)

                # Verify no logging for successful requests
                assert not mock_error.called

    def test_teardown_request_already_logged(self, app):
        """Test that teardown_request does nothing when log was already emitted."""
        with app.test_request_context("/test"):
            g.log_emitted = True  # Simulate log already emitted in after_request
            exception = ValueError("Test exception")

            with patch.object(app.logger, "error") as mock_error:
                self.logger._teardown_request(exception)

                # Verify no duplicate logging
                assert not mock_error.called

    def test_response_content_type_logging(self, app):
        """Test that response content type is properly logged."""
        with patch.object(app.logger, "info") as mock_info:
            self.client.get("/health")

            assert mock_info.called
            call_args = mock_info.call_args
            extra = call_args[1]["extra"]

            # Verify response content type is logged
            assert "http.response.content_type" in extra
            assert extra["http.response.content_type"] is not None

    def test_route_vs_path_logging(self, app):
        """Test that both route and path are logged correctly."""
        with patch.object(app.logger, "info") as mock_info:
            self.client.get("/health")

            assert mock_info.called
            call_args = mock_info.call_args
            extra = call_args[1]["extra"]

            # Verify both path and route are logged
            assert extra["http.path"] == "/health"
            assert "http.route" in extra
            # Route might be the same as path for simple routes or include rule pattern

    def test_log_emitted_flag_set(self, app):
        """Test that log_emitted flag is properly set after logging."""
        with app.test_request_context("/test"):
            g.log_start_time = 100.0
            g.log_emitted = False

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content_type = "application/json"

            with patch.object(app.logger, "info"):
                result = self.logger._after_request(mock_response)

                # Verify flag is set and response is returned unchanged
                assert g.log_emitted is True
                assert result is mock_response


class TestRequestLoggerIntegration:
    """Integration tests for RequestLogger with actual Flask routes."""

    @pytest.fixture(autouse=True)
    def setup(self, app, client):
        """Set up test environment."""
        self.app = app
        self.client = client
        # Initialize RequestLogger
        self.logger = RequestLogger(app)

    def test_full_request_lifecycle_logging(self):
        """Test complete request lifecycle with actual Flask app."""
        with patch.object(self.app.logger, "info") as mock_info:
            # Make actual request through Flask test client
            response = self.client.get("/health?debug=true")

            # Verify the response succeeded
            assert response.status_code == 200

            # Verify logging occurred
            assert mock_info.called
            call_args = mock_info.call_args
            _ = call_args[0][0]
            extra = call_args[1]["extra"]

            # Verify all required log fields are present
            required_fields = [
                "http.method",
                "http.host",
                "http.path",
                "http.route",
                "http.query_string",
                "http.request.body",
                "http.status_code",
                "http.response.content_type",
                "http.duration_ms",
            ]

            for field in required_fields:
                assert field in extra, f"Missing required field: {field}"

            # Verify field values
            assert extra["http.method"] == "GET"
            assert extra["http.path"] == "/health"
            assert extra["http.status_code"] == 200
            assert isinstance(extra["http.duration_ms"], (int, float))

    def test_middleware_preserves_response(self):
        """Test that middleware doesn't interfere with normal response handling."""
        response = self.client.get("/health")

        # Verify response is not modified by middleware
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None  # Health endpoint should return JSON

    @patch("app.middleware.request_logger.time.perf_counter")
    def test_timing_accuracy_across_requests(self, mock_perf_counter):
        """Test timing accuracy across multiple requests."""
        # Set up predictable timing
        mock_perf_counter.side_effect = [
            100.0,
            100.050,  # First request: 50ms
            200.0,
            200.150,  # Second request: 150ms
        ]

        with patch.object(self.app.logger, "info") as mock_info:
            # Make two requests
            self.client.get("/health")
            self.client.get("/health")

            # Verify both requests were logged with correct timing
            assert mock_info.call_count == 2

            # Check first request timing
            first_call = mock_info.call_args_list[0]
            assert first_call[1]["extra"]["http.duration_ms"] == 50.0

            # Check second request timing
            second_call = mock_info.call_args_list[1]
            assert second_call[1]["extra"]["http.duration_ms"] == 150.0
