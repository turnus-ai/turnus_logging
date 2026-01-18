"""
Middleware integrations for popular web frameworks.
"""

import uuid
from typing import Optional, Callable, Any, List
from .context import log_context
from .config_loader import is_safe_header, SAFE_HEADERS


class FastAPILoggingMiddleware:
    """
    FastAPI middleware that automatically injects logging context for each request.
    
    Minimal assumptions - only captures what you want:
    - Optionally captures request_id from header (or generates if specified)
    - Optionally captures method, path, client_ip
    - Custom context via extract_context callback
    
    Usage (minimal):
        from fastapi import FastAPI
        from turnus_logging.middleware import FastAPILoggingMiddleware
        
        app = FastAPI()
        app.add_middleware(FastAPILoggingMiddleware)
        # Only captures: request_id (generated), method, path
    
    Usage (custom):
        def extract_custom_context(scope, headers):
            # WARNING: Be careful with headers - avoid logging sensitive data like:
            # - Authorization tokens
            # - API keys
            # - Cookies
            # - Session IDs
            # Only extract specific, non-sensitive headers you need
            return {
                'api_version': headers.get(b'x-api-version', b'v1').decode(),
                'tenant': headers.get(b'x-tenant-id', b'').decode(),
            }
        
        app.add_middleware(
            FastAPILoggingMiddleware,
            request_id_header='X-Correlation-ID',  # Custom header name
            generate_request_id=False,  # Don't auto-generate
            include_client_ip=False,  # Skip client IP
            extract_context=extract_custom_context,  # Add custom fields
        )
    """
    
    def __init__(
        self,
        app,
        request_id_header: str = 'X-Request-ID',
        generate_request_id: bool = True,
        include_method: bool = True,
        include_path: bool = True,
        include_client_ip: bool = False,
        capture_headers: Optional[List[str]] = None,
        extract_context: Optional[Callable[[dict, dict], dict]] = None,
    ):
        """
        Args:
            app: ASGI app
            request_id_header: Header name for request ID
            generate_request_id: Generate UUID if header missing
            include_method: Include HTTP method in context
            include_path: Include request path in context
            include_client_ip: Include client IP in context
            capture_headers: List of header names to capture (validated for safety)
                           If None, uses default safe headers for debugging
            extract_context: Custom function(scope, headers) -> dict to add more fields
        """
        self.app = app
        self.request_id_header = request_id_header
        self.generate_request_id = generate_request_id
        self.include_method = include_method
        self.include_path = include_path
        self.include_client_ip = include_client_ip
        self.extract_context = extract_context
        
        # Default headers for better debugging if none specified
        if capture_headers is None:
            capture_headers = [
                'X-API-Version',
                'X-Client-Version',
                'User-Agent',
                'Content-Type',
                'Accept',
            ]
        
        # Validate and store headers to capture
        self.capture_headers = []
        if capture_headers:
            for header in capture_headers:
                if is_safe_header(header):
                    self.capture_headers.append(header.lower().encode())
                else:
                    # Warn but don't fail
                    import logging
                    logging.warning(f"Skipping unsafe header: {header}")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Build request context based on configuration
        headers = dict(scope.get("headers", []))
        context = {}
        
        # Request ID
        request_id = headers.get(self.request_id_header.lower().encode())
        if request_id:
            context['request_id'] = request_id.decode()
        elif self.generate_request_id:
            context['request_id'] = str(uuid.uuid4())
        
        # HTTP method
        if self.include_method:
            context['method'] = scope.get('method')
        
        # Request path
        if self.include_path:
            context['path'] = scope.get('path')
        
        # Client IP
        if self.include_client_ip:
            client = scope.get('client')
            if client:
                context['client_ip'] = client[0]
        
        # Capture specified headers (already validated for safety)
        for header_name in self.capture_headers:
            header_value = headers.get(header_name)
            if header_value:
                # Convert b'x-api-version' to 'api_version' for context key
                key = header_name.decode().replace('x-', '').replace('-', '_')
                context[key] = header_value.decode()
        
        # Custom context extraction
        if self.extract_context:
            try:
                custom_context = self.extract_context(scope, headers)
                if custom_context:
                    context.update(custom_context)
            except Exception:
                pass  # Don't fail request if context extraction fails
        
        # Use log_context to set context for this request
        with log_context(**context):
            await self.app(scope, receive, send)


def get_fastapi_dependency():
    """
    FastAPI dependency that extracts user context after authentication.
    
    Usage:
        from fastapi import Depends, Request
        from turnus_logging.middleware import get_fastapi_dependency
        from turnus_logging import append_context
        
        async def add_user_context(request: Request):
            if hasattr(request.state, 'user'):
                append_context({
                    'user_id': request.state.user.id,
                    'organization': request.state.user.organization
                })
        
        @app.get("/orders", dependencies=[Depends(add_user_context)])
        async def get_orders():
            logger.info("Fetching orders")  # Includes user_id, organization
    """
    pass


class FlaskLoggingMiddleware:
    """
    Flask middleware that automatically injects logging context for each request.
    
    Usage:
        from flask import Flask
        from turnus_logging.middleware import FlaskLoggingMiddleware
        
        app = Flask(__name__)
        FlaskLoggingMiddleware(app)
    """
    
    def __init__(self, app=None, extract_user: Optional[Callable] = None):
        self.extract_user = extract_user
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        from flask import request, g
        
        @app.before_request
        def setup_logging_context():
            # Extract request context
            request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
            
            context_data = {
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'client_ip': request.remote_addr,
            }
            
            # Extract user if available and custom extractor provided
            if self.extract_user:
                try:
                    user_data = self.extract_user(g)
                    if user_data:
                        context_data.update(user_data)
                except Exception:
                    pass
            
            # Store context in flask g object for cleanup
            g._logging_context = context_data
            
            # Set the context
            from turnus_logging import set_context, get_context
            current = get_context() or {}
            set_context({**current, **context_data})
        
        @app.after_request
        def cleanup_logging_context(response):
            # Context is automatically managed by contextvars and will be
            # cleaned up when the request context ends
            return response


class DjangoLoggingMiddleware:
    """
    Django middleware that automatically injects logging context for each request.
    
    Usage:
        # In settings.py MIDDLEWARE:
        MIDDLEWARE = [
            'turnus_logging.middleware.DjangoLoggingMiddleware',
            # ... other middleware
        ]
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from turnus_logging import log_context
        
        # Extract request context
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        
        context_data = {
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
        }
        
        # Add user context if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            context_data['user_id'] = str(request.user.id)
            context_data['username'] = request.user.username
        
        # Add client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            context_data['client_ip'] = x_forwarded_for.split(',')[0]
        else:
            context_data['client_ip'] = request.META.get('REMOTE_ADDR')
        
        # Process request with context
        with log_context(**context_data):
            response = self.get_response(request)
        
        return response
