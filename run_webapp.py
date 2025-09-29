#!/usr/bin/env python3
"""
Study Buddy web application launcher.

This script starts the Study Buddy web interface alongside the FastAPI backend.
"""
import uvicorn
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting Study Buddy...")
    print("📚 Web interface: http://localhost:8000")
    print("📖 API documentation: http://localhost:8000/docs")
    print("🔧 Press Ctrl+C to stop the server\n")

    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Study Buddy stopped. Take a breather – you earned it!")
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        sys.exit(1)
