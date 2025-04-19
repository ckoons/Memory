#!/usr/bin/env python3
"""
Test the AI-to-AI Communication Bridge
"""

import os
import sys
import asyncio

# Import from the communication bridge
try:
    from ai_communication import send_message, get_messages, show_conversation, run
except ImportError:
    print("Error importing AI communication bridge")
    sys.exit(1)

async def test_communication():
    """Test sending a message from Claude to Echo and checking for responses."""
    # Set client ID for Claude
    os.environ["ENGRAM_CLIENT_ID"] = "claude"
    
    print("Testing AI-to-AI Communication Bridge")
    print("-" * 50)
    
    # Send a test message from Claude to Echo
    print("\nSending test message from Claude to Echo...")
    await send_message("claude", "echo", "Hello Echo! This is a test message from Claude using our new communication bridge.")
    
    # Check for messages from Echo to Claude
    print("\nChecking for messages from Echo to Claude...")
    messages = await get_messages("ECHO_TO_CLAUDE", limit=5)
    
    if messages:
        print("Found messages from Echo:")
        for msg in messages:
            print(f"- {msg.get('content', '')}")
    else:
        print("No messages found from Echo yet.")
    
    # Show the conversation history
    print("\nShowing conversation history between Claude and Echo:")
    await show_conversation("claude", "echo", limit=5)
    
    print("-" * 50)
    print("Test completed.")

def main():
    """Run the test."""
    run(test_communication())

if __name__ == "__main__":
    main()