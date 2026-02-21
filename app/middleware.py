import os
import time
import uuid
from typing import Callable
from fastapi import Depends, Request, Response
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.auth.dependencies import get_current_user
from app.logging_config import get_logger, set_request_id, clear_context, set_user_id
from app.metrics import metrics_store


logger = get_logger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        start_time = time.time()

        # get userid
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                request.state.user = payload
                set_user_id(payload["sub"])
            except Exception:
                pass

        logger.info("request_started", method=request.method, path=request.url.path, client_host=request.client.host if request.client else None)
        try:
            response = await call_next(request) # Process the request
            duration = time.time() - start_time
            metrics_store.record(request.method, request.url.path, response.status_code, duration * 1000)
            logger.info("request_completed", method=request.method, path=request.url.path, status_code=response.status_code, duration_seconds=round(duration, 4))
            response.headers["X-Request-ID"] = request_id # sent back the request id to the client
            return response

        except Exception as e:
            duration = time.time() - start_time
            metrics_store.record(request.method, request.url.path, 500, duration * 1000)
            logger.error("request_failed", method=request.method, path=request.url.path, duration_seconds=round(duration, 4), error=str(e), exc_info=True)
            raise

        finally:
            clear_context()