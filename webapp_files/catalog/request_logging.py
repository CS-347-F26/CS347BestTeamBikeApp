import logging
import time
import uuid

logger = logging.getLogger("catalog.request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code
        log_level = (
            logging.ERROR
            if status_code >= 500
            else (logging.WARNING if status_code >= 400 else logging.INFO)
        )
        user = getattr(request, "user", None)
        user_id = user.pk if user is not None and user.is_authenticated else "-"

        logger.log(
            log_level,
            "HTTP request completed",
            extra={
                "event": "http_request",
                "method": request.method,
                "path": request.path,
                "status": status_code,
                "duration_ms": round(duration_ms, 2),
                "request_id": request_id,
                "user_id": user_id,
            },
        )
        response["X-Request-ID"] = request_id
        return response
