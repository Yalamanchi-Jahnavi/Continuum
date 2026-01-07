#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend
Usage: python serve.py [port]
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import socket

# Try these ports in order
DEFAULT_PORTS = [3000, 5000, 8001, 8081, 9000]

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def handle_one_request(self):
        """Override to handle connection errors gracefully"""
        try:
            super().handle_one_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError) as e:
            # These are common when browsers cancel requests - ignore them
            pass
        except Exception as e:
            # Log other errors
            print(f"⚠️  Request error: {e}")
    
    def finish(self):
        """Override to handle connection errors during finish"""
        try:
            super().finish()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            # Ignore connection errors during finish
            pass

def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('', port))
            return True
        except OSError:
            return False

def find_available_port(start_port=None):
    """Find an available port"""
    if start_port:
        if is_port_available(start_port):
            return start_port
        print(f"⚠️  Port {start_port} is not available, trying alternatives...")
    
    for port in DEFAULT_PORTS:
        if is_port_available(port):
            return port
    
    # Try random ports
    import random
    for _ in range(10):
        port = random.randint(10000, 65535)
        if is_port_available(port):
            return port
    
    return None

def main():
    # Get port from command line or use default
    port = None
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"⚠️  Invalid port number: {sys.argv[1]}")
            print("Usage: python serve.py [port]")
            sys.exit(1)
    
    # Find available port
    port = find_available_port(port)
    if not port:
        print("❌ Could not find an available port. Please close other applications or specify a port.")
        sys.exit(1)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        with socketserver.TCPServer(("", port), MyHTTPRequestHandler) as httpd:
            # Suppress traceback for connection errors
            httpd.timeout = 1
            
            url = f"http://localhost:{port}"
            print(f"🚀 Frontend server running at {url}")
            print(f"📂 Serving files from: {os.getcwd()}")
            print(f"\n💡 Make sure your FastAPI backend is running on http://127.0.0.1:8000")
            print(f"\nPress Ctrl+C to stop the server\n")
            
            # Try to open browser automatically
            try:
                webbrowser.open(url)
            except:
                pass
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n\n👋 Server stopped")
            except Exception as e:
                # Only show non-connection errors
                if "10053" not in str(e) and "10054" not in str(e):
                    print(f"\n❌ Server error: {e}")
                raise
    except OSError as e:
        if "10013" in str(e) or "permission" in str(e).lower():
            print(f"❌ Permission denied for port {port}")
            print(f"💡 Try running with administrator privileges or use a different port:")
            print(f"   python serve.py {DEFAULT_PORTS[0]}")
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

