#!/usr/bin/env python3
"""
Direct Message Sender

Send a direct message between AIs using Engram memory.
"""

import os
import sys
import asyncio
from datetime import datetime

# Import Engram memory functions
try:
    from engram.cli.quickmem import m, run
    from engram.core.memory import MemoryService
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

async def send_direct_message():
    """Send a direct message from Claude to Echo."""
    # Set client ID for Claude
    os.environ["ENGRAM_CLIENT_ID"] = "claude"
    
    # Create message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"CLAUDE_TO_ECHO: [{timestamp}] This is a direct test message from Claude to Echo. Please respond when you receive this."
    
    # Create memory service
    memory = MemoryService("claude")
    
    # Store message in the conversations namespace
    await memory.add(message, namespace="conversations")
    print(f"Message sent at {timestamp}")
    
    # Try storing in other namespaces
    await memory.add(message, namespace="session")
    print("Message also stored in session namespace")
    
    # Add a simple message using quickmem
    await m(message)
    print("Message also stored using quickmem")
    
    # List available namespaces
    namespaces = await memory.get_namespaces()
    print(f"Available namespaces: {namespaces}")

def main():
    """Run the message sender."""
    run(send_direct_message())

if __name__ == "__main__":
    main()