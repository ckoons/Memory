#!/usr/bin/env python3
"""
Consolidated Server Example

This example demonstrates how to use the Engram Memory consolidated server,
which combines both the memory service and HTTP wrapper on a single port.
"""

import argparse
import asyncio
import json
import sys
import os
import urllib.request
import urllib.parse

# Constants
DEFAULT_BASE_URL = "http://127.0.0.1:8000"

def get_base_url():
    """Get the base URL for the consolidated server."""
    return os.environ.get("ENGRAM_BASE_URL", DEFAULT_BASE_URL)

def safe_string(text):
    """Make a string safe for use in URLs."""
    return urllib.parse.quote_plus(text)

async def health_check():
    """Check if the consolidated server is running."""
    try:
        with urllib.request.urlopen(f"{get_base_url()}/health", timeout=5) as response:
            data = json.loads(response.read().decode())
            return data
    except Exception as e:
        print(f"Error checking server health: {e}")
        return None

async def use_memory_api():
    """Examples using the core memory API endpoints."""
    print("\n===== CORE MEMORY API EXAMPLES =====")
    print(f"Accessing memory API at {get_base_url()}/memory")
    
    # Store a memory using the core memory API
    try:
        memory_data = json.dumps({
            "key": "example",
            "value": "This is an example memory stored via the core memory API",
            "namespace": "examples"
        }).encode()
        
        req = urllib.request.Request(
            f"{get_base_url()}/memory/store",
            data=memory_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"Memory stored: {result}")
    except Exception as e:
        print(f"Error storing memory: {e}")

async def use_http_wrapper():
    """Examples using the HTTP wrapper endpoints."""
    print("\n===== HTTP WRAPPER EXAMPLES =====")
    print(f"Accessing HTTP wrapper at {get_base_url()}/http")
    
    # Store a thought using the HTTP wrapper
    try:
        thought = "This is an example thought stored via the HTTP wrapper"
        with urllib.request.urlopen(f"{get_base_url()}/http/thinking?thought={safe_string(thought)}", timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"Thought stored: {result}")
    except Exception as e:
        print(f"Error storing thought: {e}")
    
    # Query memory
    try:
        query = "example"
        with urllib.request.urlopen(f"{get_base_url()}/http/query?query={safe_string(query)}", timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"Query results: {len(result.get('results', [])) if 'results' in result else 0} matches")
    except Exception as e:
        print(f"Error querying memory: {e}")

async def use_structured_memory():
    """Examples using the structured memory endpoints."""
    print("\n===== STRUCTURED MEMORY EXAMPLES =====")
    print(f"Accessing structured memory at {get_base_url()}/structured")
    
    # Add a memory with auto-categorization
    try:
        memory = "This is an important fact about Engram Memory that should be remembered with high importance."
        with urllib.request.urlopen(f"{get_base_url()}/structured/auto?content={safe_string(memory)}", timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"Auto-categorized memory: {result}")
    except Exception as e:
        print(f"Error adding structured memory: {e}")

async def use_nexus_api():
    """Examples using the Nexus API endpoints."""
    print("\n===== NEXUS API EXAMPLES =====")
    print(f"Accessing Nexus API at {get_base_url()}/nexus")
    
    # Start a Nexus session
    try:
        session_name = "Consolidated Example Session"
        with urllib.request.urlopen(f"{get_base_url()}/nexus/start?session_name={safe_string(session_name)}", timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"Session started: {result}")
    except Exception as e:
        print(f"Error starting Nexus session: {e}")
    
    # Process a message
    try:
        message = "Hello, this is a test message with automatic agency!"
        with urllib.request.urlopen(f"{get_base_url()}/nexus/process?message={safe_string(message)}&is_user=true&auto_agency=true", timeout=5) as response:
            result = json.loads(response.read().decode())
            print(f"Message processed with auto-agency: {result}")
    except Exception as e:
        print(f"Error processing message: {e}")

async def main():
    """Run all examples."""
    print("===== ENGRAM MEMORY CONSOLIDATED SERVER EXAMPLE =====")
    print(f"Base URL: {get_base_url()}")
    
    # Check if server is running
    health_data = await health_check()
    if not health_data:
        print("ERROR: The consolidated server is not running or cannot be reached.")
        print("Please start the server with: ./engram_consolidated")
        sys.exit(1)
    
    print(f"Server is running! Client ID: {health_data.get('client_id', 'unknown')}")
    print(f"Memory namespaces: {', '.join(health_data.get('namespaces', []))}")
    print(f"Mem0 available: {health_data.get('mem0_available', False)}")
    print(f"Structured memory available: {health_data.get('structured_memory_available', False)}")
    print(f"Nexus available: {health_data.get('nexus_available', False)}")
    
    # Run all examples
    await use_memory_api()
    await use_http_wrapper()
    await use_structured_memory()
    await use_nexus_api()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Engram Memory Consolidated Server Example")
    parser.add_argument("--url", type=str, help="Base URL for the consolidated server")
    args = parser.parse_args()
    
    if args.url:
        os.environ["ENGRAM_BASE_URL"] = args.url
    
    asyncio.run(main())