#!/usr/bin/env python3
"""
Simple production entry point for URL Shortener
For development, use: python run_local.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Production should use gunicorn, not Flask dev server
    print("⚠️  For production, use: gunicorn run:app")
    print("For development, use: python run_local.py")
    app.run()