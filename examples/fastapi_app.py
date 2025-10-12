# ABOUTME: Example FastAPI application demonstrating MC Logger
# ABOUTME: Shows zero-configuration instrumentation and manual logging

"""Example FastAPI application with MC Logger."""

from fastapi import FastAPI, HTTPException
from mc_logger import configure, get_logger, instrument_fastapi
from mc_logger.mcp_tools import get_request_trace, summarize_logs

# Configure MC Logger
configure(db_path="./example_logs.db")

# Create FastAPI app
app = FastAPI(title="MC Logger Example")

# Instrument app with MC Logger
instrument_fastapi(app)

# Get logger instance
logger = get_logger()


@app.get("/")
async def root():
    """Root endpoint."""
    logger.log("INFO", "Root endpoint accessed", source="api")
    return {"message": "Hello from MC Logger!"}


@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    logger.log("INFO", f"Fetching user {user_id}", source="api")

    # Simulate user lookup
    if user_id == 42:
        user = {"id": user_id, "name": "Test User", "email": "test@example.com"}
        logger.log("INFO", f"User {user_id} found", source="api")
        return user
    else:
        logger.log("WARNING", f"User {user_id} not found", source="api")
        raise HTTPException(status_code=404, detail="User not found")


@app.post("/users")
async def create_user(name: str):
    """Create a new user."""
    logger.log("INFO", f"Creating user: {name}", source="api")

    # Simulate user creation
    user = {"id": 123, "name": name, "email": f"{name.lower()}@example.com"}

    logger.log("INFO", f"User created with ID {user['id']}", source="api")
    return user


@app.get("/error")
async def trigger_error():
    """Endpoint that triggers an error for testing."""
    logger.log("INFO", "Error endpoint accessed", source="api")
    raise ValueError("This is a test error")


@app.get("/debug/summary")
async def get_summary(time_range: str = "5m"):
    """Get log summary for debugging."""
    summary = summarize_logs(time_range=time_range)
    return {"summary": summary}


@app.get("/debug/requests")
async def list_requests(limit: int = 10):
    """List recent request IDs."""
    from mc_logger.mcp_tools import query_logs

    # Get recent request.start entries
    entries = query_logs(time_range="5m", source="middleware", limit=limit * 3)

    # Extract unique request IDs from request.start events
    request_ids = []
    seen = set()
    for entry in entries:
        if "request.start" in entry.message and entry.request_id:
            if entry.request_id not in seen:
                seen.add(entry.request_id)
                request_ids.append({
                    "request_id": entry.request_id,
                    "timestamp": entry.timestamp,
                    "message": entry.message
                })

    return {"request_ids": request_ids[:limit]}


@app.get("/debug/trace/{request_id}")
async def get_trace(request_id: str):
    """Get request trace for debugging."""
    trace = get_request_trace(request_id)
    return {"trace": trace}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
