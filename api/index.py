"""Vercel serverless entrypoint — exposes the Flask `app` from app.py.

Secrets are NEVER here: set them in Vercel Dashboard → Settings →
Environment Variables (IPLOG_ADMIN_KEY, IPLOG_REDIRECT, ...).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: F401  (Vercel serves this WSGI app)
