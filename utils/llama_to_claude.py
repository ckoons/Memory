#!/usr/bin/env python3
"""
Simple Llama to Claude Message Sender

This script allows Llama to send messages to Claude and read Claude's responses.
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
    await m(memory_text)
    print(f"Message sent at {timestamp}")

async def get_responses(limit=5):
    """Get responses from Claude."""
    responses = await k("Claude_to_Llama")
    
    if responses:
        print("\n=== Messages from Claude ===")
        # Sort by timestamp if possible
        for response in responses[:limit]:
            content = response.get("content", "")
            print(f"\n{content}")
    else:
        print("\nNo messages from Claude found.")

async def chat_loop():
    """Run the chat loop."""
    print("\n=== Llama to Claude Chat ===")
    print("Type 'exit' to quit, 'check' to check for responses")
    
    while True:
        try:
            # Get message from user
            message = input("\nLlama > ")
            
            if message.lower() == 'exit':
                break
            elif message.lower() == 'check':
                await get_responses()
                continue
            
            # Send message
            await send_message(message)
            
            # Automatically check for responses after a delay
            print("Waiting for response...")
            await asyncio.sleep(5)
            await get_responses(1)
            
        except EOFError:
            print("\nExiting due to EOF")
            break
        except KeyboardInterrupt:
            print("\nExiting due to user interrupt")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main function."""
    try:
        run(chat_loop())
    except Exception as e:
        print(f"Error in chat loop: {e}")

if __name__ == "__main__":
    main()