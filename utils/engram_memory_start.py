#!/usr/bin/env python3
"""
Engram - Simplified Memory Session Starter

This is a single file solution for starting AI sessions with memory.
Simply import this file at the beginning of a Claude session.

Usage:
  from engram_memory_start import start_memory
  start_memory()  # Loads previous memories and initializes session
  
  # Or with a specific session name
  start_memory("Project Research Session")
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import time
from typing import Dict, List, Any, Optional

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default HTTP URL for the memory service
DEFAULT_HTTP_URL = "http://127.0.0.1:8000/http"

def _get_http_url():
    """Get the HTTP URL for the memory service."""
    return os.environ.get("ENGRAM_HTTP_URL", DEFAULT_HTTP_URL)

def _safe_string(text: str) -> str:
    """URL-encode a string to make it safe for GET requests."""
    return urllib.parse.quote_plus(text)

def check_service():
    """Check if the memory service is running."""
    try:
        url = f"{_get_http_url()}/health"
        with urllib.request.urlopen(url, timeout=2) as response:
            health_data = json.loads(response.read().decode())
            return health_data.get("status") == "ok"
    except Exception:
        return False

def start_service():
    """Try to start the memory service."""
    try:
        print(f"{YELLOW}Memory service is not running. Attempting to start...{RESET}")
        
        # Try to find the service start script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        check_script = os.path.join(script_dir, "engram_check.py")
        
        if os.path.exists(check_script):
            import subprocess
            subprocess.run([check_script, "--start"], check=True)
            time.sleep(2)  # Wait for services to start
            return check_service()
        else:
            print(f"{RED}Could not find engram_check.py script to start services{RESET}")
            return False
    except Exception as e:
        print(f"{RED}Error starting memory service: {e}{RESET}")
        return False

def load_memories(limit=3):
    """Load previous session memories."""
    try:
        url = f"{_get_http_url()}/load?limit={limit}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                content = result.get("content", [])
                if content:
                    print(f"{GREEN}✅ Loaded {len(content)} session memories:{RESET}")
                    for i, item in enumerate(content):
                        print(f"  {i+1}. {item}")
                    return content
                else:
                    print(f"{YELLOW}No session memories found{RESET}")
                    return []
            else:
                print(f"{RED}Failed to load session memory{RESET}")
                return []
    except Exception as e:
        print(f"{RED}Error loading session memory: {e}{RESET}")
        return []

def start_session(name=None):
    """Start a new session and record it in memory."""
    try:
        # Format session message
        if name:
            session_message = f"Starting new session: {name}"
        else:
            session_message = "Starting new session"
            
        # Store the message
        url = f"{_get_http_url()}/write?content={_safe_string(session_message)}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"{GREEN}✅ Session started: {session_message}{RESET}")
                return True
            else:
                print(f"{RED}Failed to record session start{RESET}")
                return False
    except Exception as e:
        print(f"{RED}Error starting session: {e}{RESET}")
        return False

def think(thought):
    """Store a thought in thinking namespace."""
    try:
        url = f"{_get_http_url()}/thinking?thought={_safe_string(thought)}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            return result.get("success", False)
    except Exception:
        return False

def start_memory(session_name=None):
    """
    One-step function to start a Claude session with memory.
    
    Args:
        session_name: Optional name for this session
    """
    print(f"\n{BOLD}{BLUE}===== Engram Memory Session ====={RESET}")
    
    # Check if service is running
    if not check_service():
        # Try to start the service
        if not start_service():
            print(f"{RED}Could not start memory service. Memory functions will not be available.{RESET}")
            return False
    
    print(f"{GREEN}✅ Memory service is running{RESET}")
    
    # Load previous memories
    memories = load_memories()
    
    # Start new session
    start_session(session_name)
    
    # If we found previous memories, add a reflective thought
    if memories:
        think("I should maintain continuity from previous sessions and remember key information.")
    
    print(f"{BLUE}Memory functions are now available:{RESET}")
    print(f"  - from engram.cli.quickmem import * (for all functions)")
    print(f"  - Use m() to search memories, t() for thoughts, r() to remember")
    print(f"{BOLD}{BLUE}===================================={RESET}\n")
    
    return True

if __name__ == "__main__":
    # Allow running directly as a script
    session_name = sys.argv[1] if len(sys.argv) > 1 else None
    start_memory(session_name)