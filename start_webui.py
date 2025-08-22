#!/usr/bin/env python3
"""
Quick start script for YKGen Web UI.

This script starts the web UI server directly without setup checks.
Use this if you've already run setup_webui.py or installed dependencies manually.
"""

import sys
import os
from pathlib import Path

def main():
    """Start the YKGen Web UI server."""
    print("🚀 Starting YKGen Web UI...")
    print("   Server will be available at: http://localhost:8080")
    print("   Press Ctrl+C to stop the server\n")
    
    try:
        import uvicorn
        
        # Check if webui.py exists
        webui_file = Path("webui.py")
        if not webui_file.exists():
            print("❌ webui.py not found in current directory")
            print("   Make sure you're running this from the YKGen project root")
            sys.exit(1)
        
        # Start the server
        uvicorn.run(
            "webui:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        print("❌ uvicorn not installed")
        print("   Install with: pip install uvicorn[standard]")
        print("   Or run: python setup_webui.py")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 Web UI stopped")
        
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()