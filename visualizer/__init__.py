#!/usr/bin/env python3
"""
Fifth Referee - Main Application Runner
Run this file to start both the API server and Dash analytics dashboard
"""
import sys
import os
import threading
import time
import webbrowser
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_api_server():
    """Run the FastAPI server"""
    try:
        import uvicorn
        from interfaces.api import api

        print("🚀 Starting FastAPI server...")
        uvicorn.run(
            api,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        print("💡 Make sure uvicorn is installed: pip install uvicorn")

def run_dash_app():
    """Run the Dash analytics dashboard"""
    try:
        # Give the API server a moment to start
        time.sleep(3)

        import dash
        from dash import dcc, html, Input, Output, callback, dash_table
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd
        import requests
        import numpy as np

        # Import the dash app from interfaces
        from interfaces.dash_app import app

        print("📊 Starting Dash analytics dashboard...")
        print("🌐 Dashboard will be available at: http://localhost:8050")

        # Open browser automatically
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open('http://localhost:8050')

        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

        app.run(
            debug=True,
            port=8050,
            host="127.0.0.1"
        )

    except Exception as e:
        print(f"❌ Error starting Dash app: {e}")
        print("💡 Make sure required packages are installed:")
        print("   pip install dash plotly pandas requests numpy")

def main():
    """Main function to coordinate both services"""
    print("=" * 60)
    print("⚽ FIFTH REFEREE - Analytics Platform")
    print("=" * 60)
    print()

    # Check if required packages are installed
    required_packages = [
        ('uvicorn', 'uvicorn'),
        ('fastapi', 'fastapi'),
        ('dash', 'dash'),
        ('plotly', 'plotly'),
        ('pandas', 'pandas'),
        ('requests', 'requests')
    ]

    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print(f"\n💡 Install with: pip install {' '.join(missing_packages)}")
        return

    print("✅ All required packages found!")
    print()
    print("🎯 Starting services...")
    print("   📡 FastAPI Server: http://localhost:8000")
    print("   📊 Dash Dashboard: http://localhost:8050")
    print("   📚 API Docs: http://localhost:8000/docs")
    print()
    print("🛑 Press Ctrl+C to stop both services")
    print("=" * 60)

    # Start API server in a separate thread
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    # Start Dash app in main thread (so Ctrl+C works properly)
    try:
        run_dash_app()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        print("👋 Goodbye!")

def run_api_only():
    """Run only the FastAPI server"""
    print("🚀 Starting FastAPI server only...")
    try:
        import uvicorn
        from interfaces.api import api

        uvicorn.run(
            api,
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down API server...")

def run_dash_only():
    """Run only the Dash dashboard"""
    print("📊 Starting Dash dashboard only...")
    try:
        from interfaces.dash_app import app
        app.run(debug=True, port=8050, host="127.0.0.1")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Dash app...")

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "api":
            run_api_only()
        elif sys.argv[1] == "dash":
            run_dash_only()
        elif sys.argv[1] == "help":
            print("Fifth Referee - Usage:")
            print("  python __init__.py        # Run both API and Dash")
            print("  python __init__.py api    # Run only API server")
            print("  python __init__.py dash   # Run only Dash app")
            print("  python __init__.py help   # Show this help")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use 'python __init__.py help' for usage information")
    else:
        main()
