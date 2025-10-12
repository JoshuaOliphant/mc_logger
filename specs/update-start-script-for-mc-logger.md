# Chore: Update start.sh Script for MC Logger Project

## Chore Description
The current `scripts/start.sh` script is from a different project (Natural Language SQL Interface) that expects a client/server architecture with an npm frontend (on port 5173) and Python backend (on port 8000). The MC Logger project has a different architecture:

1. **MC Logger Example App**: FastAPI application (`examples/fastapi_app.py`) running on port 8000
2. **ADW Webhook Server**: FastAPI webhook endpoint (`adws/trigger_webhook.py`) running on port 8001 (optional)
3. **ADW Cron Monitor**: Background polling service (`adws/trigger_cron.py`) that monitors GitHub issues (optional)

The script needs to be updated to:
- Start the MC Logger example FastAPI application
- Optionally start the ADW webhook server (for GitHub webhook integration)
- Remove references to npm/frontend and Natural Language SQL Interface
- Remove .env checks that don't apply to this project
- Update port information and documentation

## Relevant Files
Use these files to resolve the chore:

- `scripts/start.sh` - The main startup script that needs to be updated. Currently starts a client/server architecture with npm frontend, needs to start MC Logger example app and optionally ADW webhook server.
- `examples/fastapi_app.py` - The MC Logger example FastAPI application that demonstrates the logging system, runs on port 8000 with uvicorn.
- `adws/trigger_webhook.py` - Optional ADW webhook server that listens for GitHub events on port 8001 (default), can be started alongside the example app.
- `scripts/stop_apps.sh` - Companion script that stops services, needs minor updates to reflect new service names in output messages.
- `README.md` - Project documentation showing how to run the example app (`uv run python examples/fastapi_app.py`).
- `adws/README.md` - ADW documentation showing how to run webhook server (`uv run trigger_webhook.py`).

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Update `scripts/start.sh` to Start MC Logger Services
- Remove all references to "Natural Language SQL Interface" and replace with "MC Logger"
- Remove .env file existence check (lines 15-23) since MC Logger doesn't require .env for the example app
- Remove frontend/client startup logic (lines 58-71) since there is no npm frontend
- Update backend startup to run `examples/fastapi_app.py` instead of `app/server/server.py`
- Change working directory from `$PROJECT_ROOT/app/server` to `$PROJECT_ROOT`
- Add optional ADW webhook server startup with a flag (e.g., `--with-adw` or `--adw-webhook`)
- Update success message to show only relevant ports (8000 for example app, 8001 if ADW webhook is enabled)
- Remove "Frontend: http://localhost:5173" from output
- Update API Docs URL to point to example app: "http://localhost:8000/docs"
- Add usage instructions at the top of the script showing optional flags
- Ensure proper cleanup of both services (example app and webhook server if running)

### 2. Update `scripts/stop_apps.sh` to Match New Architecture
- Change "Natural Language SQL Interface" to "MC Logger" in output messages
- Update comments to reflect that it stops MC Logger example app and ADW services
- Verify ports 8000 and 8001 are still being killed (correct for this project)
- Remove port 5173 from the kill list since there's no frontend
- Ensure webhook server process name is still being killed (trigger_webhook.py is correct)

### 3. Test the Updated Scripts
- Run `scripts/start.sh` to verify it starts the example app correctly
- Verify the example app is accessible at http://localhost:8000
- Verify the OpenAPI docs are accessible at http://localhost:8000/docs
- Test stopping services with `scripts/stop_apps.sh`
- Test starting with ADW webhook flag (if implemented) to verify it starts on port 8001
- Verify Ctrl+C properly stops all services when using `start.sh`

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest tests/ -v` - Run all tests to ensure no regressions in the MC Logger core functionality
- `./scripts/start.sh &` - Start the services in background to verify script works
- `sleep 5 && curl -s http://localhost:8000/ | jq .` - Verify example app is running and responding
- `curl -s http://localhost:8000/docs | head -20` - Verify OpenAPI docs are accessible
- `./scripts/stop_apps.sh` - Stop all services to verify cleanup works
- `sleep 2 && ! lsof -ti:8000,8001` - Verify ports are released after stopping

## Notes
- The MC Logger example app (`examples/fastapi_app.py`) creates a SQLite database at `./example_logs.db` when it runs
- The example app has debug endpoints at `/debug/summary` and `/debug/trace/{request_id}` that are useful for testing
- The ADW webhook server is optional and only needed if users want to integrate with GitHub webhooks for automated issue processing
- Both services use `uv run` for execution, which is the modern Python package runner
- The original script's signal handling and cleanup functions are good and should be preserved
- Consider adding a `--help` flag to show usage information
