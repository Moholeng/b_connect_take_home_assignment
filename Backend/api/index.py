"""Vercel serverless entrypoint.

Vercel's Python runtime serves the ASGI ``app`` it finds in this file.
We simply re-export the FastAPI application defined in ``app.main`` so the
whole API (sync, wifi, insights, agent routers) runs as one function.
"""

from app.main import app  # noqa: F401  (re-exported for the Vercel runtime)
