#!/usr/bin/env python3
"""
Run the Fusion Cashflow Dashboard with static file serving enabled.
This allows the logo.png to be served properly.
"""

import os
import sys
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers import DirectoryHandler

def main():
    # Get the directory containing this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the dashboard file
    dashboard_path = os.path.join(current_dir, "src", "fusion_cashflow", "ui")
    
    # Path to static files
    static_path = os.path.join(current_dir, "src", "fusion_cashflow", "ui", "static")
    
    print(f"Dashboard path: {dashboard_path}")
    print(f"Static files path: {static_path}")
    
    # Check if static directory exists
    if not os.path.exists(static_path):
        print(f"Warning: Static directory not found at {static_path}")
        return
    
    # Check if logo exists
    logo_path = os.path.join(static_path, "logo.png")
    if os.path.exists(logo_path):
        print(f"✅ Logo found at: {logo_path}")
    else:
        print(f"❌ Logo not found at: {logo_path}")
        return
    
    # Create the Bokeh server with static file serving
    try:
        # Use Bokeh Server API directly instead of subprocess
        from bokeh.application.handlers import ScriptHandler
        from bokeh.application import Application
        from tornado.web import StaticFileHandler
        
        # Create application from the dashboard script
        handler = ScriptHandler(filename=os.path.join(dashboard_path, "dashboard.py"))
        app = Application(handler)
        
        # Create server with custom static file handler to avoid conflicts
        server = Server({'/dashboard': app}, 
                       port=5011,
                       allow_websocket_origin=["localhost:5011"],
                       extra_patterns=[
                           # Serve our assets at /assets/ to avoid conflicts with Bokeh's /static/
                           (r"/assets/(.*)", StaticFileHandler, {"path": static_path}),
                       ])
        
        print("✅ Starting Bokeh server with static file serving...")
        print("📂 Static files served from:", static_path, "at /assets/")
        print("🌐 Dashboard URL: http://localhost:5011/dashboard")
        
        server.start()
        server.io_loop.add_callback(server.show, "/dashboard")
        server.io_loop.start()
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
