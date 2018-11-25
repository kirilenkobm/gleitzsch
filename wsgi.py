#!/usr/bin/env python3
"""Wsgi entry point."""
from app import app as application

if __name__ == "__main__":
    application.run()
