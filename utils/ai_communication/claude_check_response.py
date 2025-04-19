#!/usr/bin/env python3
"""
Non-interactive Claude Response Checker

This script allows Claude to check for responses from Echo in the Engram memory system.
"""

import os
import sys
import asyncio
from datetime import datetime

# Import Engram memory functions
try:
    from engram.cli.quickmem import run, k
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

async def check_echo_responses():
    """Check for responses from Echo without user input."""
    # Set client ID for Claude
    os.environ["ENGRAM_CLIENT_ID"] = "claude"
    
    print("Checking for messages from Echo...")
    
    # First check Ollama's memory file directly
    home_dir = os.path.expanduser("~")
    engram_dir = os.path.join(home_dir, ".engram")
    ollama_memory_file = os.path.join(engram_dir, "ollama-memories.json")
    
    if os.path.exists(ollama_memory_file):
        print(f"Reading Ollama's memory file: {ollama_memory_file}")
        try:
            import json
            with open(ollama_memory_file, "r") as f:
                ollama_data = json.load(f)
            
            # Find messages from Echo to Claude
            echo_responses = []
            
            for namespace, memories in ollama_data.items():
                for memory in memories:
                    content = memory.get("content", "")
                    if "ECHO_TO_CLAUDE" in content:
                        echo_responses.append(memory)
            
            if echo_responses:
                # Sort by timestamp if possible
                def extract_timestamp(memory):
                    content = memory.get("content", "")
                    try:
                        timestamp = content.split("[")[1].split("]")[0]
                        return timestamp
                    except (IndexError, ValueError):
                        return ""
                
                responses = sorted(echo_responses, key=extract_timestamp, reverse=True)
            else:
                print("No responses found from Echo in Ollama's memory file.")
                # Try search API as fallback
                responses = await k("ECHO_TO_CLAUDE")
        except Exception as e:
            print(f"Error reading Ollama's memory file: {e}")
            responses = await k("ECHO_TO_CLAUDE")
    else:
        print("Ollama's memory file not found, using search API instead.")
        responses = await k("ECHO_TO_CLAUDE")
    
    if not responses:
        print("No responses found from Echo.")
        return
    
    # Display found responses
    print(f"Found {len(responses)} response(s) from Echo:")
    for i, response in enumerate(responses):
        content = response.get("content", "")
        print(f"\n{i+1}. {content}")

def main():
    """Run the response checker."""
    run(check_echo_responses())

if __name__ == "__main__":
    main()