#!/usr/bin/env python3
"""
AI-to-AI Communication Bridge

This script provides a robust communication channel between different AI models
using Engram's memory system. It allows for:
- Sending messages between AIs with consistent tags
- Retrieving messages with proper threading
- Viewing conversation history
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
import json
from pathlib import Path

# Import Engram memory functions
try:
    from engram.cli.quickmem import m, k, run, s
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

# Standard memory tags
CLAUDE_TO_ECHO = "CLAUDE_TO_ECHO"
ECHO_TO_CLAUDE = "ECHO_TO_CLAUDE"

async def send_message(sender, recipient, message, thread_id=None):
    """Send a message from one AI to another."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Determine the appropriate tag based on sender/recipient
    if sender.lower() == "claude" and recipient.lower() == "echo":
        tag = CLAUDE_TO_ECHO
    elif sender.lower() == "echo" and recipient.lower() == "claude":
        tag = ECHO_TO_CLAUDE
    else:
        tag = f"{sender.upper()}_TO_{recipient.upper()}"
    
    # Add thread_id if provided
    thread_part = f" [Thread: {thread_id}]" if thread_id else ""
    
    # Include tag information in the message itself to make search easier
    # Format: TAG: [TIMESTAMP] [Thread: ID] TAG:SENDER:RECIPIENT {message}
    memory_text = f"{tag}: [{timestamp}]{thread_part} {tag}:{sender}:{recipient} {message}"
    
    await m(memory_text)
    
    print(f"Message sent from {sender} to {recipient} at {timestamp}")
    return {"status": "sent", "timestamp": timestamp, "thread_id": thread_id}

async def get_messages(tag, limit=10, thread_id=None):
    """Get messages with a specific tag and optional thread ID."""
    try:
        # Search by tag in the content
        messages = await k(tag)
        
        if not messages:
            return []
        
        # Filter by thread_id if provided
        if thread_id:
            filtered_messages = []
            for message in messages:
                content = message.get("content", "")
                if f"[Thread: {thread_id}]" in content:
                    filtered_messages.append(message)
            messages = filtered_messages
        
        # Sort by timestamp (newest first)
        def get_timestamp(message):
            content = message.get("content", "")
            try:
                timestamp = content.split("[")[1].split("]")[0]
                return timestamp
            except (IndexError, ValueError):
                return ""
            
        return sorted(messages, key=get_timestamp, reverse=True)[:limit]
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

async def show_conversation(sender, recipient, limit=10, thread_id=None):
    """Show the conversation between two AIs with proper threading."""
    # Determine tags based on participants
    if (sender.lower() == "claude" and recipient.lower() == "echo") or (sender.lower() == "echo" and recipient.lower() == "claude"):
        tag1 = CLAUDE_TO_ECHO
        tag2 = ECHO_TO_CLAUDE
    else:
        tag1 = f"{sender.upper()}_TO_{recipient.upper()}"
        tag2 = f"{recipient.upper()}_TO_{sender.upper()}"
    
    # Get messages in both directions
    messages1 = await get_messages(tag1, limit*2, thread_id)
    messages2 = await get_messages(tag2, limit*2, thread_id)
    
    # Combine messages
    all_messages = messages1 + messages2
    
    # Remove duplicates by ID
    seen_ids = set()
    unique_messages = []
    for message in all_messages:
        message_id = message.get("id", "")
        if message_id and message_id not in seen_ids:
            seen_ids.add(message_id)
            unique_messages.append(message)
    
    # Extract timestamps for sorting
    def extract_timestamp(message):
        content = message.get("content", "")
        try:
            # Extract timestamp between first set of square brackets
            timestamp_str = content.split("[")[1].split("]")[0]
            return timestamp_str
        except (IndexError, ValueError):
            return ""
    
    # Sort messages by timestamp (newest first)
    sorted_messages = sorted(unique_messages, key=extract_timestamp, reverse=True)
    
    # Display the conversation
    print(f"\n=== Conversation between {sender} and {recipient} ===")
    if thread_id:
        print(f"Thread ID: {thread_id}")
        
    if not sorted_messages:
        print("No messages found.")
        return []
    
    # Format and display messages
    for i, message in enumerate(sorted_messages[:limit]):
        content = message.get("content", "")
        
        # Extract sender information from the content
        # Format is: TAG: [TIMESTAMP] [Thread: ID] TAG:SENDER:RECIPIENT message
        try:
            # First, detect which tag is being used
            if CLAUDE_TO_ECHO in content:
                tag = CLAUDE_TO_ECHO
                default_sender = "Claude"
            elif ECHO_TO_CLAUDE in content:
                tag = ECHO_TO_CLAUDE
                default_sender = "Echo"
            else:
                tag = content.split(":")[0].strip()
                default_sender = tag.split("_TO_")[0].capitalize()
            
            # Try to extract sender from the tag:sender:recipient format
            tag_parts = content.split("] ")[-1].split(" ", 1)[0].split(":")
            if len(tag_parts) >= 2:
                msg_sender = tag_parts[1].capitalize()
            else:
                msg_sender = default_sender
        except:
            msg_sender = "Unknown"
        
        # Extract timestamp
        try:
            timestamp = content.split("[")[1].split("]")[0]
        except:
            timestamp = "Unknown time"
        
        # Extract the actual message content
        try:
            # Skip tag, timestamp, thread ID, and tag info
            parts = content.split("] ")
            if len(parts) > 1:
                # Get everything after timestamp and thread ID
                remaining = parts[-1]
                # Remove the TAG:SENDER:RECIPIENT part
                if ":" in remaining:
                    tag_info = remaining.split(" ", 1)[0]
                    if len(tag_info.split(":")) >= 2:
                        msg_content = remaining.split(" ", 1)[1]
                    else:
                        msg_content = remaining
                else:
                    msg_content = remaining
            else:
                msg_content = content
        except:
            msg_content = content
        
        print(f"\n{i+1}. {msg_sender} ({timestamp}):")
        print(f"   {msg_content.strip()}")
    
    return sorted_messages

async def ai_chat(sender, interactive=True):
    """Run an interactive or single-shot AI chat session."""
    # Set Engram client ID based on sender
    os.environ["ENGRAM_CLIENT_ID"] = sender.lower()
    
    # Determine recipient based on sender
    if sender.lower() == "claude":
        recipient = "echo"
    else:
        recipient = "claude"
    
    # Check if memory service is running
    try:
        status = s()
        print(f"Memory service status: {status}")
    except Exception as e:
        print(f"Error checking memory status: {e}")
        sys.exit(1)
    
    if interactive:
        print(f"\n=== {sender} to {recipient} Chat ===")
        print("Type 'exit' to quit, 'check' to check for responses")
        print("Use 'thread:[id]' to start or continue a specific thread")
        
        active_thread = None
        
        while True:
            try:
                # Get message from user
                if active_thread:
                    prompt = f"\n{sender} (Thread: {active_thread}) > "
                else:
                    prompt = f"\n{sender} > "
                
                message = input(prompt)
                
                # Handle special commands
                if message.lower() == 'exit':
                    break
                elif message.lower() == 'check':
                    await show_conversation(sender, recipient, limit=5, thread_id=active_thread)
                    continue
                elif message.lower().startswith('thread:'):
                    active_thread = message.split(':', 1)[1].strip()
                    print(f"Active thread set to: {active_thread}")
                    continue
                
                # Send message
                await send_message(sender, recipient, message, thread_id=active_thread)
                
                # Automatically check for responses after a delay
                print("Checking for recent messages...")
                await asyncio.sleep(1)
                await show_conversation(sender, recipient, limit=3, thread_id=active_thread)
                
            except EOFError:
                print("\nExiting due to EOF")
                break
            except KeyboardInterrupt:
                print("\nExiting due to user interrupt")
                break
            except Exception as e:
                print(f"Error: {e}")
    else:
        # Non-interactive mode - show recent conversation
        await show_conversation(sender, recipient, limit=5)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="AI-to-AI Communication Bridge")
    parser.add_argument("sender", type=str, help="Sender AI (claude or echo)")
    parser.add_argument("--message", type=str, help="Message to send (for non-interactive mode)")
    parser.add_argument("--thread", type=str, help="Thread ID for conversation threading")
    parser.add_argument("--check", action="store_true", help="Check for messages without sending")
    
    args = parser.parse_args()
    
    # Validate sender
    if args.sender.lower() not in ["claude", "echo"]:
        print("Error: Sender must be either 'claude' or 'echo'")
        sys.exit(1)
    
    try:
        if args.check:
            # Just check for messages
            recipient = "echo" if args.sender.lower() == "claude" else "claude"
            run(show_conversation(args.sender, recipient, thread_id=args.thread))
        elif args.message:
            # Send a single message
            recipient = "echo" if args.sender.lower() == "claude" else "claude"
            run(send_message(args.sender, recipient, args.message, thread_id=args.thread))
            run(show_conversation(args.sender, recipient, limit=3, thread_id=args.thread))
        else:
            # Interactive mode
            run(ai_chat(args.sender))
    except Exception as e:
        print(f"Error in communication bridge: {e}")

if __name__ == "__main__":
    main()