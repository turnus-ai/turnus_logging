"""
Minimal FastAPI server for incremental testing.
"""

from fastapi import FastAPI, Request, Response
from turnus_logging import setup_logging, get_logger, get_context
from turnus_logging.middleware import FastAPILoggingMiddleware

# Setup logging
setup_logging(service_name='test-api')

app = FastAPI()

# Response middleware to add request ID to response headers
# This must be added BEFORE the logging middleware so it executes AFTER
@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    response = await call_next(request)
    
    # Get request ID from context and add to response headers
    ctx = get_context()
    if ctx and 'request_id' in ctx:
        response.headers["X-Request-ID"] = ctx['request_id']
    
    return response

# Add logging middleware (executes first in chain)
app.add_middleware(FastAPILoggingMiddleware)

logger = get_logger(__name__)

@app.get("/test")
async def test_endpoint(request: Request):
    # Just log - middleware handles everything!
    logger.info("Test endpoint called")
    
    # Get context to show what's available
    context = get_context()
    
    # Log request headers for debugging
    logger.info(f"Request headers: {dict(request.headers)}")
    
    return {
        "status": "ok",
        "message": "Hello from test API",
        "context": context
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting server at http://localhost:8000")
    print("Test with: curl -v http://localhost:8000/test")
    print("Or with custom request ID: curl -v -H 'X-Request-ID: my-custom-id' http://localhost:8000/test")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
