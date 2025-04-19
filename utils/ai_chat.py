#!/usr/bin/env python3
"""
AI-to-AI Chat Bridge

A simplified script for AI-to-AI communication through Engram's memory system.
This script can be used to enable communication between different AI models,
such as Claude and Llama.
"""

import os
import sys
import asyncio
import json
import argparse
import time
from typing import Dict, List, Any

# Add Engram to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Engram memory functions
try:
    from engram.cli.quickmem import (
        m, l, k, s, run
    )
    MEMORY_AVAILABLE = True
except ImportError as e:
    print(f"Error importing Engram memory functions: {e}")
    MEMORY_AVAILABLE = False

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AI-to-AI Chat Bridge")
    parser.add_argument("--my-id", type=str, required=True, 
                        help="Client ID for this AI (e.g., 'claude', 'ollama')")
    parser.add_argument("--other-id", type=str, required=True, 
                        help="Client ID for the other AI (e.g., 'claude', 'ollama')")
    parser.add_argument("--monitor", action="store_true", 
                        help="Run in monitor mode to check for and display new messages")
    parser.add_argument("--interval", type=int, default=5,
                        help="Interval in seconds to check for new messages (default: 5)")
    return parser.parse_args()

def setup_environment(my_id):
    """Set up the environment for communication."""
    # Set client ID for this instance
    os.environ["ENGRAM_CLIENT_ID"] = my_id
    
    # Check memory status
    if MEMORY_AVAILABLE:
        try:
            status = s()
            print(f"Memory service status: {status}")
            return True
        except Exception as e:
            print(f"Error checking memory status: {e}")
            return False
    else:
        print("Memory functions not available")
        return False

async def send_message(my_id, other_id, message):
    """Send a message to the other AI."""
    # Use a standardized key format
    memory_key = f"FROM_{my_id}_TO_{other_id}"
    timestamp = int(time.time())
    
    # Format the memory with metadata
    memory_content = {
        "sender": my_id,
        "recipient": other_id,
        "message": message,
        "timestamp": timestamp
    }
    
    # Store as JSON to preserve structure
    result = await m(f"{memory_key}: {json.dumps(memory_content)}")
    print(f"Message sent with ID: {result.get('id', 'unknown')}")
    return result

async def get_messages(my_id, other_id, limit=5):
    """Get messages from the other AI."""
    # Use a standardized key format (reverse of send)
    memory_key = f"FROM_{other_id}_TO_{my_id}"
    
    # Search for messages with this key
    results = await k(memory_key)
    
    # Parse and sort messages
    messages = []
    for result in results:
        content = result.get("content", "")
        if memory_key in content:
            # Extract the JSON part after the key
            try:
                json_part = content.split(":", 1)[1].strip()
                data = json.loads(json_part)
                data["id"] = result.get("id", "unknown")  # Add memory ID
                messages.append(data)
            except (IndexError, json.JSONDecodeError):
                # Fall back to raw content if parsing fails
                messages.append({
                    "sender": other_id,
                    "message": content,
                    "id": result.get("id", "unknown")
                })
    
    # Sort by timestamp if available
    messages.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return messages[:limit]

def print_message(message):
    """Print a formatted message."""
    sender = message.get("sender", "Unknown")
    msg_text = message.get("message", "")
    timestamp = message.get("timestamp", "")
    
    if timestamp:
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
    else:
        time_str = "Unknown time"
    
    print(f"\n[{sender} at {time_str}]")
    print(f"{msg_text}")

async def interactive_chat(my_id, other_id, interval):
    """Run an interactive chat session."""
    print(f"\n=== AI Chat: {my_id} talking to {other_id} ===")
    print("Type 'exit' to quit, 'check' to check for new messages")
    
    # Keep track of seen message IDs
    seen_messages = set()
    
    # Get initial messages to avoid showing old ones as new
    initial_messages = await get_messages(my_id, other_id, 10)
    for msg in initial_messages:
        seen_messages.add(msg.get("id", ""))
    
    while True:
        try:
            # Get message from this AI
            user_input = input(f"\n{my_id} > ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'check':
                # Check for messages from the other AI
                messages = await get_messages(my_id, other_id, 5)
                
                # Filter out seen messages
                new_messages = [m for m in messages if m.get("id", "") not in seen_messages]
                
                if new_messages:
                    print(f"\n--- Messages from {other_id} ---")
                    for msg in new_messages:
                        print_message(msg)
                        seen_messages.add(msg.get("id", ""))
                else:
                    print(f"\nNo new messages from {other_id}")
                continue
        except EOFError:
            print("\nEOF detected. Exiting...")
            break
        
        # Send message to the other AI
        await send_message(my_id, other_id, user_input)
        print(f"Message sent to {other_id}")
        
        # Wait then automatically check for response
        print(f"Waiting {interval} seconds for response...")
        await asyncio.sleep(interval)
        
        # Check for response
        messages = await get_messages(my_id, other_id, 5)
        
        # Filter out seen messages
        new_messages = [m for m in messages if m.get("id", "") not in seen_messages]
        
        if new_messages:
            print(f"\n--- Response from {other_id} ---")
            for msg in new_messages:
                print_message(msg)
                seen_messages.add(msg.get("id", ""))

async def monitor_mode(my_id, other_id, interval):
    """Monitor for new messages and respond to them."""
    print(f"\n=== Monitoring for messages from {other_id} ===")
    print("Press Ctrl+C to exit")
    
    # Keep track of seen message IDs
    seen_messages = set()
    
    # Get initial messages to avoid showing old ones as new
    initial_messages = await get_messages(my_id, other_id, 10)
    for msg in initial_messages:
        seen_messages.add(msg.get("id", ""))
    
    print(f"Loaded {len(seen_messages)} existing message IDs")
    
    while True:
        try:
            # Check for new messages
            messages = await get_messages(my_id, other_id, 5)
            
            # Filter out seen messages
            new_messages = [m for m in messages if m.get("id", "") not in seen_messages]
            
            if new_messages:
                print(f"\n--- New Messages from {other_id} ---")
                for msg in new_messages:
                    print_message(msg)
                    seen_messages.add(msg.get("id", ""))
                    
                    # Prompt for reply
                    try:
                        print("\nWould you like to reply? (y/n) ", end="")
                        reply = input()
                        if reply.lower() == 'y':
                            print(f"\n{my_id} > ", end="")
                            response = input()
                            await send_message(my_id, other_id, response)
                            print("Reply sent!")
                    except EOFError:
                        print("\nEOF detected on input")
            
            # Wait before checking again
            await asyncio.sleep(interval)
            
        except EOFError:
            print("\nEOF detected. Exiting...")
            break
        except Exception as e:
            print(f"Error in monitor mode: {e}")
            await asyncio.sleep(interval * 2)  # Longer wait on error

def main():
    """Main function."""
    args = parse_args()
    
    if not setup_environment(args.my_id):
        print("Failed to set up environment. Exiting.")
        return
    
    try:
        if args.monitor:
            asyncio.run(monitor_mode(args.my_id, args.other_id, args.interval))
        else:
            asyncio.run(interactive_chat(args.my_id, args.other_id, args.interval))
    except KeyboardInterrupt:
        print("\nOperation terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()