# asgi.py

from hypercorn.middleware import AsyncioWSGIMiddleware
from app import app

asgi_app = AsyncioWSGIMiddleware(app)

