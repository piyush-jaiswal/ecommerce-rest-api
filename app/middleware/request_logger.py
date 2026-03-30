import json
import time
from urllib.parse import parse_qs, urlparse

from flask import Flask, Request, Response, g, request


class RequestLogger:
    def __init__(self, app: Flask):
        self.app = app
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)

    def _before_request(self):
        g.log_start_time = time.perf_counter()
        g.log_emitted = False

    def _after_request(self, response: Response):
        duration_ms = RequestLogger._duration_ms()
        host = urlparse(request.base_url).hostname
        message = f"[{host}] {request.method} {request.path} -> {response.status_code} ({duration_ms}ms)"

        extra = {
            "http.method": request.method,
            "http.host": host,
            "http.path": request.path,
            "http.route": str(request.url_rule or request.path),
            "http.query_string": DataScrubber.scrub_query_string(request),
            "http.request.body": DataScrubber.scrub_body(request),
            "http.status_code": response.status_code,
            "http.response.content_type": response.content_type,
            "http.duration_ms": duration_ms,
        }

        if response.status_code >= 400:
            self.app.logger.warning(message, extra=extra)
        else:
            self.app.logger.info(message, extra=extra)

        g.log_emitted = True
        return response

    # Only runs when an unhandled exception bypassed after_request
    def _teardown_request(self, exc):
        if exc is None or g.get("log_emitted"):
            return

        duration_ms = RequestLogger._duration_ms()
        host = urlparse(request.base_url).hostname
        message = f"[{host}] {request.method} {request.path} -> 500 ({duration_ms}ms)"

        self.app.logger.error(
            message,
            extra={
                "http.method": request.method,
                "http.host": host,
                "http.path": request.path,
                "http.query_string": DataScrubber.scrub_query_string(request),
                "http.request.body": DataScrubber.scrub_body(request),
                "http.status_code": 500,
                "http.duration_ms": duration_ms,
                "error.type": type(exc).__name__,
                "error.message": str(exc),
            },
            exc_info=exc,
        )

    @staticmethod
    def _duration_ms():
        return round((time.perf_counter() - g.log_start_time) * 1000, 2)


class DataScrubber:
    # Fields whose values are replaced with SENSITIVE_DATA_REPLACEMENT
    SENSITIVE_KEYS = frozenset(
        {
            "password",
            "passwd",
            "secret",
            "token",
            "api_key",
            "apikey",
            "access_token",
            "refresh_token",
            "authorization",
            "auth",
            "private_key",
        }
    )
    _DATA_REPLACEMENT = "[redacted]"
    _MAX_BYTES = 4096

    @staticmethod
    def scrub_query_string(req: Request):
        raw = req.query_string.decode("utf-8", errors="replace")
        if not raw:
            return ""

        parsed = parse_qs(raw, keep_blank_values=True)
        return json.dumps(
            {
                k: [DataScrubber._DATA_REPLACEMENT] * len(v)
                if k.lower() in DataScrubber.SENSITIVE_KEYS
                else v
                for k, v in parsed.items()
            }
        )

    @staticmethod
    def scrub_body(req: Request):
        try:
            raw = req.get_data(as_text=True)
        except Exception:
            return "<unreadable>"

        if not raw:
            return ""

        content_type = req.content_type or ""

        if "application/json" in content_type:
            try:
                data = json.loads(raw)
                scrubbed = DataScrubber._scrub_json(data)
                result = json.dumps(scrubbed)
            except json.JSONDecodeError:
                result = "<invalid json>"

        elif "application/x-www-form-urlencoded" in content_type:
            parsed = parse_qs(raw, keep_blank_values=True)
            scrubbed = {
                k: [DataScrubber._DATA_REPLACEMENT] * len(v)
                if k.lower() in DataScrubber.SENSITIVE_KEYS
                else v
                for k, v in parsed.items()
            }
            result = json.dumps(scrubbed)

        else:
            return "<unsupported format>"

        # truncate if too big
        if len(result) > DataScrubber._MAX_BYTES:
            result = result[: DataScrubber._MAX_BYTES] + " … [truncated]"

        return result

    @staticmethod
    def _scrub_json(data, _depth=1):
        """Recursively redact sensitive keys in a parsed JSON object."""
        if _depth > 20:
            return "<too deeply nested>"

        if isinstance(data, dict):
            return {
                k: DataScrubber._DATA_REPLACEMENT
                if k.lower() in DataScrubber.SENSITIVE_KEYS
                else DataScrubber._scrub_json(v, _depth + 1)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [DataScrubber._scrub_json(item, _depth + 1) for item in data]

        return data
