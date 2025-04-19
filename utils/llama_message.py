#!/usr/bin/env python3
"""
Llama Message Sender

Send a message from Llama to Claude using command line arguments.
"""

import os
import sys
import asyncio
from datetime import datetime

# Import Engram memory functions
try:
    from engram.cli.quickmem import m, k, run
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

# Set client ID
os.environ["ENGRAM_CLIENT_ID"] = "ollama"

async def send_message(message):
    """Send a message to Claude."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    memory_text = f"Llama_to_Claude: [{timestamp}] {message}"
    result = await m(memory_text)
    print(f"Message sent at {timestamp}")
    return result

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python llama_message.py \"Your message to Claude\"")
        return
    
    message = sys.argv[1]
    print(f"Sending message to Claude: {message}")
    
    try:
        run(send_message(message))
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    main()