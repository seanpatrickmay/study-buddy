#!/usr/bin/env python3
"""
Study Bot Web Application Launcher

This script starts the Study Bot web application with the integrated frontend.
"""
import uvicorn
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting Study Bot Web Application...")
    print("📚 Access the web interface at: http://localhost:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
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
        print("\n👋 Study Bot stopped. Thank you for using our service!")
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        sys.exit(1)