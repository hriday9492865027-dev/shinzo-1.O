import sys
from pathlib import Path

# Add project root to sys.path so 'app' package is discoverable
root_path = Path(__file__).parent.parent.resolve()
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from app.api.main import app  # ASGI app for Vercel Serverless
