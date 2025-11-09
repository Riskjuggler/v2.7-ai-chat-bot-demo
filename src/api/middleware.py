"""Security middleware for localhost-only access."""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class LocalhostOnlyMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce localhost-only access."""

    async def dispatch(self, request: Request, call_next):
        """
        Check if request is from localhost, reject if not.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response from next handler or 403 error
        """
        # Get client host
        client_host = request.client.host if request.client else None

        # Allow localhost and loopback addresses
        allowed_hosts = ["127.0.0.1", "localhost", "::1", "testclient"]

        if client_host not in allowed_hosts:
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "detail": "API only accessible from localhost",
                },
            )

        # Request is from localhost, proceed
        response = await call_next(request)
        return response
