#\!/usr/bin/env python3
import urllib.request
import sys

def test_url(url):
    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                print(f"✅ Successfully connected to {url}")
                return True
            else:
                print(f"❌ Failed to connect to {url} - Status: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Error connecting to {url}: {e}")
        return False

if __name__ == "__main__":
    urls = [
        "http://localhost:8000/health",  # Memory Bridge
        "http://localhost:8001/health",  # HTTP Wrapper
        "http://localhost:8002/"         # Web UI
    ]
    
    success = True
    for url in urls:
        if not test_url(url):
            success = False
    
    sys.exit(0 if success else 1)
