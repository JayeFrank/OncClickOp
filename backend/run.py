# backend/run.py
"""
Development server runner for the Desktop App Framework
This file makes it easy to start your FastAPI backend with a single command
"""

import uvicorn
import sys
import os

# Add the current directory to Python path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """
    Start the FastAPI development server
    
    The server will:
    - Run on http://localhost:8000
    - Auto-reload when you make code changes
    - Show detailed logs for debugging
    """
    print("🚀 Starting Desktop App Framework Backend...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Auto-reload is enabled - save files to see changes")
    print("\n" + "="*50 + "\n")
    
    # Configure and run the server
    uvicorn.run(
        "app.main:app",  # Path to your FastAPI app instance
        host="0.0.0.0",  # Listen on all network interfaces
        port=8000,       # Port number
        reload=True,     # Enable auto-reload for development
        log_level="info" # Show informational logs
    )

if __name__ == "__main__":
    main()