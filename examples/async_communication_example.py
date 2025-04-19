#!/usr/bin/env python3
"""
Asynchronous Communication Example

This script demonstrates how to use the asynchronous communication protocol
for robust message passing between AI systems.
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, project_root)

# Try to import the async communication functions
try:
    from engram.cli.comm_quickmem import (
        # Full function names
        send_async,
        receive_async,
        broadcast_async,
        reply_async,
        async_status,
        cleanup_async,
        
        # Short aliases
        sa, ra, ba, rp, acs, cla
    )
    
    print("✅ Successfully imported async communication functions")
except ImportError as e:
    print(f"❌ Error importing async communication functions: {e}")
    print("Make sure you run this from the project root or install the package.")
    sys.exit(1)

# Example: Send an async message
async def example_send():
    """Demonstrate sending an async message."""
    print("\n🔹 Example: Sending an async message")
    
    # Get client ID from environment or use default
    client_id = os.environ.get("ENGRAM_CLIENT_ID", "claude")
    print(f"- Using client ID: {client_id}")
    
    # Send a message to all instances
    message_content = {
        "text": "Hello from the async communication protocol!",
        "timestamp": datetime.now().isoformat(),
        "source": f"example_send() in async_communication_example.py",
        "data": {
            "sample": "This is a complex data structure that can be sent",
            "values": [1, 2, 3, 4, 5],
            "nested": {
                "key": "value",
                "bool": True
            }
        }
    }
    
    # Send with default parameters (to="all", priority=2, etc.)
    message_id = await send_async(message_content)
    
    if message_id:
        print(f"- ✅ Message sent with ID: {message_id}")
        return message_id
    else:
        print(f"- ❌ Failed to send message")
        return None

# Example: Receive async messages
async def example_receive():
    """Demonstrate receiving async messages."""
    print("\n🔹 Example: Receiving async messages")
    
    # Receive messages with default parameters
    messages = await receive_async()
    
    if messages:
        print(f"- ✅ Received {len(messages)} messages")
        
        # Show the first message in detail
        if len(messages) > 0:
            first_msg = messages[0]
            print("\nFirst message details:")
            print(f"- ID: {first_msg.get('message_id')}")
            print(f"- Sender: {first_msg.get('sender_id')}")
            print(f"- Type: {first_msg.get('message_type')}")
            print(f"- Priority: {first_msg.get('priority')}")
            print(f"- Status: {first_msg.get('status')}")
            
            # Show content preview
            content = first_msg.get('content')
            if isinstance(content, dict):
                # Format dict for display
                print(f"- Content: {json.dumps(content, indent=2)[:200]}...")
            else:
                print(f"- Content: {str(content)[:200]}...")
        
        return messages
    else:
        print(f"- ℹ️ No messages received")
        return []

# Example: Check async communication status
async def example_status():
    """Demonstrate checking async communication status."""
    print("\n🔹 Example: Checking async communication status")
    
    status = await async_status()
    
    if status:
        print(f"- ✅ Got status information")
        
        # Show some interesting stats
        queue_stats = status.get("queue_stats", {})
        if queue_stats:
            total = queue_stats.get("total_count", 0)
            pending = queue_stats.get("pending_count", 0)
            delivered = queue_stats.get("delivered_count", 0)
            processed = queue_stats.get("processed_count", 0)
            
            print(f"\nMessage statistics:")
            print(f"- Total messages: {total}")
            print(f"- Pending: {pending}")
            print(f"- Delivered: {delivered}")
            print(f"- Processed: {processed}")
            
            # Priority distribution
            priority_dist = queue_stats.get("priority_distribution", {})
            if priority_dist:
                print(f"\nPriority distribution:")
                for priority, count in priority_dist.items():
                    print(f"- Priority {priority}: {count} messages")
        
        return status
    else:
        print(f"- ❌ Failed to get status")
        return None

# Example: Broadcast to all instances
async def example_broadcast():
    """Demonstrate broadcasting to all instances."""
    print("\n🔹 Example: Broadcasting to all instances")
    
    # Create a broadcast message
    broadcast_content = {
        "announcement": "Important system notification",
        "timestamp": datetime.now().isoformat(),
        "details": "This is a broadcast message to all Claude instances"
    }
    
    # Send with higher priority (4 = URGENT)
    message_id = await broadcast_async(
        content=broadcast_content,
        priority=4,
        ttl_seconds=3600  # Expires after 1 hour
    )
    
    if message_id:
        print(f"- ✅ Broadcast sent with ID: {message_id}")
        return message_id
    else:
        print(f"- ❌ Failed to send broadcast")
        return None

# Example: Reply to a message
async def example_reply(parent_id):
    """Demonstrate replying to a message."""
    print(f"\n🔹 Example: Replying to message {parent_id}")
    
    if not parent_id:
        print("- ❌ No parent message ID provided")
        return None
    
    # Create reply content
    reply_content = {
        "response": "This is a reply to your message",
        "timestamp": datetime.now().isoformat(),
        "referenced_id": parent_id,
        "additional_info": "This tests the enhanced reply functionality"
    }
    
    # Create custom metadata
    metadata = {
        "example": "reply_test",
        "test_timestamp": datetime.now().isoformat(),
        "test_purpose": "Testing enhanced reply functionality"
    }
    
    # Send reply with custom metadata
    message_id = await reply_async(
        parent_id=parent_id,
        content=reply_content,
        metadata=metadata
    )
    
    if message_id:
        print(f"- ✅ Reply sent with ID: {message_id}")
        
        # Try to retrieve the reply we just sent
        print("- Checking if reply was properly stored...")
        received_messages = await receive_async(include_processed=True, mark_as_delivered=False)
        
        # Look for our reply in the received messages
        found = False
        for msg in received_messages:
            if msg.get("message_id") == message_id:
                found = True
                print("  ✓ Reply found in message store")
                break
                
        if not found:
            print("  ⚠️ Reply not found in received messages (this may be normal if delivery is delayed)")
        
        return message_id
    else:
        print(f"- ❌ Failed to send reply")
        return None

# Example: Clean up expired messages
async def example_cleanup():
    """Demonstrate cleaning up expired messages."""
    print("\n🔹 Example: Cleaning up expired messages")
    
    count = await cleanup_async()
    
    print(f"- ✅ Cleaned up {count} expired messages")
    return count

# Run all examples
async def run_examples():
    """Run all examples to demonstrate the async communication protocol."""
    print("=" * 60)
    print("ASYNCHRONOUS COMMUNICATION PROTOCOL EXAMPLES")
    print("=" * 60)
    print("\nThis script demonstrates the async communication protocol")
    print("for robust message passing between AI systems.")
    
    # Check status before examples
    await example_status()
    
    # Send a message and get its ID
    message_id = await example_send()
    
    # Give the system a moment to process
    print("\nWaiting for message processing...")
    await asyncio.sleep(1)
    
    # Try to receive messages
    messages = await example_receive()
    
    # If we successfully sent a message, try replying to it
    if message_id:
        await example_reply(message_id)
    
    # Broadcast a message
    await example_broadcast()
    
    # Check status after sending messages
    await example_status()
    
    # Clean up any expired messages
    await example_cleanup()
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETED")
    print("=" * 60)

# Main function
def main():
    """Main entry point."""
    # Set up asyncio event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # Run examples
    loop.run_until_complete(run_examples())

if __name__ == "__main__":
    main()