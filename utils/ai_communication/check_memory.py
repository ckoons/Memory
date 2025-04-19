#!/usr/bin/env python3
"""
Check Memory Tags

This script checks for AI-to-AI communication messages in the Engram memory system.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Tags to check
CLAUDE_TO_ECHO = "CLAUDE_TO_ECHO"
ECHO_TO_CLAUDE = "ECHO_TO_CLAUDE"

async def check_memory():
    """Check for communication messages in memory."""
    # Get home directory
    home_dir = os.path.expanduser("~")
    
    # Check the memory files directly
    engram_dir = Path(f"{home_dir}/.engram")
    
    # Look for client memory files
    memory_files = {
        "claude": engram_dir / "claude-memories.json",
        "ollama": engram_dir / "ollama-memories.json"
    }
    
    print(f"Checking for AI-to-AI communication messages...")
    
    for client, file_path in memory_files.items():
        if file_path.exists():
            print(f"\n=== {client.capitalize()} Memory File ===")
            try:
                with open(file_path, "r") as f:
                    memory_data = json.load(f)
                
                # Search for message tags
                for namespace, memories in memory_data.items():
                    claude_to_echo_found = False
                    echo_to_claude_found = False
                    
                    for memory in memories:
                        content = memory.get("content", "")
                        
                        if CLAUDE_TO_ECHO in content:
                            if not claude_to_echo_found:
                                print(f"\nFound messages from Claude to Echo in namespace {namespace}:")
                                claude_to_echo_found = True
                            print(f"- {content}")
                        
                        if ECHO_TO_CLAUDE in content:
                            if not echo_to_claude_found:
                                print(f"\nFound messages from Echo to Claude in namespace {namespace}:")
                                echo_to_claude_found = True
                            print(f"- {content}")
                    
                    if not (claude_to_echo_found or echo_to_claude_found):
                        print(f"No communication messages found in namespace {namespace}")
            except Exception as e:
                print(f"Error reading memory file: {e}")
        else:
            print(f"\n{client.capitalize()} memory file not found at: {file_path}")

def main():
    """Run the memory check."""
    asyncio.run(check_memory())

if __name__ == "__main__":
    main()