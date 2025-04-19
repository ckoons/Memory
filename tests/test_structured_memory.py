#!/usr/bin/env python3
"""
Test script for the structured memory system.
"""

import asyncio
from engram.cli.quickmem import memory_digest, start_nexus, process_message, auto_remember, end_nexus
from engram.cli.quickmem import mem, think, write

async def main():
    # Test structured memory features
    
    print("===== Testing quickmem functions =====")
    
    # Test basic memory operations
    print("\nStoring a thought...")
    think_result = think("This is a test thought for structured memory")
    print(f"Think result: {think_result}")
    
    print("\nStoring in long-term memory...")
    mem_result = mem("structured memory test")
    print(f"Memory search result: {mem_result}")
    
    print("\nWriting session memory...")
    write_result = write("This is a test session memory for structured memory system")
    print(f"Write result: {write_result}")
    
    # Test Nexus features
    print("\n===== Testing Nexus features =====")
    
    print("\nGetting memory digest...")
    digest = await memory_digest(max_memories=5, include_private=False)
    print(f"Memory digest received, length: {len(digest) if digest else 0} characters")
    
    print("\nStarting Nexus session...")
    start_result = await start_nexus(session_name="Test Session")
    print(f"Session started, response length: {len(start_result) if start_result else 0} characters")
    
    print("\nProcessing user message...")
    user_message = "Let's discuss the structured memory system implementation"
    context = await process_message(message=user_message, is_user=True)
    print(f"Processed message with context, length: {len(context) if context else 0} characters")
    
    print("\nProcessing assistant message...")
    assistant_message = "The structured memory system uses file-based storage with importance ranking"
    assistant_result = await process_message(message=assistant_message, is_user=False)
    print(f"Assistant message processed: {assistant_result}")
    
    print("\nAuto-remembering information...")
    memory_id = await auto_remember(content="The structured memory system has importance levels from 1 to 5")
    print(f"Memory stored with ID: {memory_id}")
    
    print("\nEnding Nexus session...")
    end_result = await end_nexus(summary="Completed testing the structured memory system")
    print(f"Session ended: {end_result}")
    
    print("\n===== Test completed =====")

if __name__ == "__main__":
    asyncio.run(main())