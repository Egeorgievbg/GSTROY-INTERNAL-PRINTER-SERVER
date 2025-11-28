import logging
from time import perf_counter

from flask import Flask, Response, request


def register_cors(app: Flask) -> None:
    """Apply permissive CORS headers for all responses."""

    logger = logging.getLogger("gstroy.server")

    @app.before_request
    def log_request_start():
        request.environ.setdefault("gstroy.request_start", perf_counter())
        logger.info("Incoming %s %s from %s", request.method, request.path, request.remote_addr)

    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
        response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type")
        start = request.environ.get("gstroy.request_start")
        if start:
            duration = perf_counter() - start
            logger.info("Responded %s %s %s in %.3fs", request.method, request.path, response.status_code, duration)
        return response
