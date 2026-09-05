"""
Vercel serverless entry point for Shinzo AI.

All imports are wrapped in try/except so that if something fails,
we return a 500 with the ACTUAL error — not a generic crash.
"""
import sys
import traceback
from pathlib import Path

# Add project root to sys.path so 'app' package is discoverable
root_path = Path(__file__).parent.parent.resolve()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

_import_error = None

try:
    from mangum import Mangum
    from app.api.main import app
    handler = Mangum(app, lifespan="auto")
except Exception as _e:
    _import_error = traceback.format_exc()

    # Fallback: return the actual error so we can read it in Vercel logs
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    _fallback_app = FastAPI()

    @_fallback_app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
    async def error_handler(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Import failed — see details",
                "details": _import_error,
            }
        )

    from mangum import Mangum as _Mangum  # type: ignore
    handler = _Mangum(_fallback_app, lifespan="off")
