import os
import sys

# Ensure project directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

# cPanel CloudLinux Passenger compatibility
# Converts ASGI FastAPI app to WSGI for standard Passenger environments
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    application = app
