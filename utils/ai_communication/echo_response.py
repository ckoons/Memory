#!/usr/bin/env python3
"""
Echo Response Generator

This script emulates Echo responding to Claude's messages in the Engram memory system.
"""

import os
import sys
import asyncio
from datetime import datetime

# Import Engram memory functions
try:
    from engram.cli.quickmem import run
    from engram.core.memory import MemoryService
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

# Memory tags
CLAUDE_TO_ECHO = "CLAUDE_TO_ECHO"
ECHO_TO_CLAUDE = "ECHO_TO_CLAUDE"

async def respond_to_claude():
    """Emulate Echo responding to Claude's messages."""
    # Set client ID for Echo
    os.environ["ENGRAM_CLIENT_ID"] = "ollama"
    
    # Create memory service
    memory = MemoryService("ollama")
    
    # Search for messages from Claude by using the shared memory file
    print("Searching for messages from Claude...")
    
    # First check Claude's memory file directly
    home_dir = os.path.expanduser("~")
    engram_dir = os.path.join(home_dir, ".engram")
    claude_memory_file = os.path.join(engram_dir, "claude-memories.json")
    
    if os.path.exists(claude_memory_file):
        print(f"Reading Claude's memory file: {claude_memory_file}")
        try:
            import json
            with open(claude_memory_file, "r") as f:
                claude_data = json.load(f)
            
            # Find messages in conversations namespace
            found_messages = []
            
            for namespace, memories in claude_data.items():
                for memory in memories:
                    content = memory.get("content", "")
                    if CLAUDE_TO_ECHO in content:
                        found_messages.append(memory)
            
            if not found_messages:
                print("No messages found from Claude in the memory file.")
                return
            
            # Use the found messages
            claude_messages = {"results": found_messages, "count": len(found_messages)}
        except Exception as e:
            print(f"Error reading Claude's memory file: {e}")
            claude_messages = await memory.search(CLAUDE_TO_ECHO)
    else:
        print("Claude's memory file not found, using search API instead.")
        claude_messages = await memory.search(CLAUDE_TO_ECHO)
    
    if not claude_messages.get("results"):
        print("No messages found from Claude.")
        return
    
    # Display found messages
    print(f"Found {claude_messages.get('count', 0)} messages from Claude:")
    for i, message in enumerate(claude_messages.get("results", [])):
        content = message.get("content", "")
        print(f"{i+1}. {content}")
    
    # Create a response as Echo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = f"{ECHO_TO_CLAUDE}: [{timestamp}] Hello Claude! This is Echo responding to your message. I've received your test message successfully. The communication bridge is working!"
    
    # Store the response using the CLI function
    from engram.cli.quickmem import m
    await m(response)
    print(f"\nResponse sent at {timestamp}")
    print(f"Response: {response}")
    
    # Try to store in the file directly to ensure it's saved
    try:
        # Create the ollama memory file if it doesn't exist
        ollama_memory_file = os.path.join(engram_dir, "ollama-memories.json")
        
        if os.path.exists(ollama_memory_file):
            # Read existing data
            with open(ollama_memory_file, "r") as f:
                ollama_data = json.load(f)
        else:
            # Create new data structure
            ollama_data = {
                "conversations": [],
                "thinking": [],
                "longterm": [],
                "projects": [],
                "compartments": [],
                "session": []
            }
        
        # Create memory object
        memory_obj = {
            "id": f"conversation-{int(datetime.now().timestamp())}-{hash(response) % 10000}",
            "content": response,
            "metadata": {
                "timestamp": timestamp,
                "client_id": "ollama"
            }
        }
        
        # Add to conversations namespace
        ollama_data["conversations"].append(memory_obj)
        
        # Also add to session namespace
        session_obj = memory_obj.copy()
        session_obj["id"] = f"session-{int(datetime.now().timestamp())}-{hash(response) % 10000}"
        ollama_data["session"].append(session_obj)
        
        # Save the file
        with open(ollama_memory_file, "w") as f:
            json.dump(ollama_data, f, indent=2)
        
        print("Response also saved directly to ollama memory file")
    except Exception as e:
        print(f"Error saving to memory file: {e}")

def main():
    """Run the Echo response generator."""
    run(respond_to_claude())

if __name__ == "__main__":
    main()