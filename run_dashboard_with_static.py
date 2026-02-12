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
    
    # Get allowed WebSocket origins from environment or use wildcard for deployment
    # For production, set BOKEH_ALLOW_WS_ORIGIN to specific domain (e.g., "myapp.example.com:5011")
    allowed_origins = os.environ.get('BOKEH_ALLOW_WS_ORIGIN', '*').split(',')
    if allowed_origins == ['*']:
        print("Warning: Allowing WebSocket connections from ANY origin. Set BOKEH_ALLOW_WS_ORIGIN for production.")
    
    print(f"Dashboard path: {dashboard_path}")
    print(f"Static files path: {static_path}")
    print(f"Allowed WebSocket origins: {allowed_origins}")
    
    # Check if static directory exists
    if not os.path.exists(static_path):
        print(f"Warning: Static directory not found at {static_path}")
        return
    
    # Check if logo exists
    logo_path = os.path.join(static_path, "logo.png")
    if os.path.exists(logo_path):
        print(f"Logo found at: {logo_path}")
    else:
        print(f"Logo not found at: {logo_path}")
        return
    
    # Create the Bokeh server with static file serving
    try:
        # Use Bokeh Server API directly instead of subprocess
        from bokeh.application.handlers import ScriptHandler
        from bokeh.application import Application
        from tornado.web import StaticFileHandler
        
        # Custom static file handler with no-cache headers to prevent stale content
        class NoCacheStaticFileHandler(StaticFileHandler):
            def set_extra_headers(self, path):
                # Prevent caching to avoid duplicate dashboard issues on first load
                self.set_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.set_header("Pragma", "no-cache")
                self.set_header("Expires", "0")
        
        # Create application from the dashboard script
        handler = ScriptHandler(filename=os.path.join(dashboard_path, "dashboard.py"))
        app = Application(handler)
        
        # Create server with custom static file handler
        # Get port from environment variable (Render sets PORT automatically)
        port = int(os.environ.get('PORT', 5011))
        
        server = Server({'/dashboard': app}, 
                       port=port,
                       allow_websocket_origin=allowed_origins,
                       extra_patterns=[
                           # Serve our assets at /assets/ to avoid conflicts with Bokeh's /static/
                           (r"/assets/(.*)", NoCacheStaticFileHandler, {"path": static_path}),
                       ])
        
        print("Starting Bokeh server with static file serving...")
        print("Static files served from:", static_path, "at /assets/")
        print(f"Dashboard URL: http://localhost:{port}/dashboard")
        
        server.start()
        # Don't auto-open browser in production
        if os.environ.get('PORT'):
            print("Production mode - server started")
        else:
            server.io_loop.add_callback(server.show, "/dashboard")
        server.io_loop.start()
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()
