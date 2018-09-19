#!/usr/bin/env python3
"""Run flask server."""
from app import app

if __name__ == '__main__':
    app.run(host="0.0.0.0")
