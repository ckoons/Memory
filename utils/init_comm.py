#!/usr/bin/env python3
"""
Simple initialization script for Claude-to-Claude communication functions
"""

import os
import sys

# Get client ID from environment
client_id = os.environ.get("ENGRAM_CLIENT_ID", "unknown")
print(f"Client ID: {client_id}")

# Add project directory to Python path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Claude-to-Claude communication functions
try:
    from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
    print("✅ Communication functions loaded!")
    print("Functions available:")
    print("  sm() - Send message")
    print("  gm() - Get messages")
    print("  ho() - Handoff message")
    print("  cc() - Create context")
    print("  lc() - List contexts")
    print("  sc() - Send to context")
    print("  gc() - Get context messages")
    print("  cs() - Check communication status")
    print("  wi() - Who am I (get client ID)")
    
    # Display identity
    print(f"\nYour identity: {wi()}")
    
    # Check communication status
    print("\nCommunication status:")
    comm_status = cs()
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Failed to load communication functions.")