#!/usr/bin/env python3
"""
Simple FastAPI startup without database migrations.
For testing purposes only.
"""

import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting EduAnalytics API (simple mode)...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

