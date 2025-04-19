#!/usr/bin/env python3
"""
Engram - Session End Helper

This is a simple script to save a summary of the current session 
before ending an AI conversation.

Usage:
  from engram_memory_end import end_session
  end_session("We implemented memory auto-loading features")
  
  # Or with auto-generated summary
  end_session()
"""

import os
import sys
import json
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# Default HTTP URL for the memory service
DEFAULT_HTTP_URL = "http://127.0.0.1:8000/http"

def _get_http_url():
    """Get the HTTP URL for the memory service."""
    return os.environ.get("ENGRAM_HTTP_URL", DEFAULT_HTTP_URL)

def _safe_string(text: str) -> str:
    """URL-encode a string to make it safe for GET requests."""
    return urllib.parse.quote_plus(text)

def end_session(summary: str = None):
    """
    End the current Claude session with an optional summary.
    
    Args:
        summary: Optional summary of what was accomplished. If None,
                 a default summary will be created.
    """
    # Default summary if none provided
    if summary is None:
        summary = "Session ended. We worked on Claude Memory Bridge features for maintaining continuity across sessions."
    
    try:
        # Store the session summary
        full_summary = f"Session summary: {summary}"
        url = f"{_get_http_url()}/write?content={_safe_string(full_summary)}"
        with urllib.request.urlopen(url) as response:
            result = json.loads(response.read().decode())
            
            if result.get("success", False):
                print(f"\n{GREEN}✅ Session summary stored{RESET}")
                print(f"{GREEN}✓ Summary: {summary}{RESET}")
                return True
            else:
                print(f"\n{YELLOW}⚠️ Failed to store session summary{RESET}")
                return False
    except Exception as e:
        print(f"\n{RED}❌ Error ending session: {e}{RESET}")
        return False

if __name__ == "__main__":
    # Allow running directly with command line arguments
    summary = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    end_session(summary)