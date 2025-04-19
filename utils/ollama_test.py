#!/usr/bin/env python3
"""
Ollama Test Script

This script runs a non-interactive test of the Ollama and Engram integration
to verify that memory functions are working correctly.
"""

import os
import sys
import argparse
import json
from engram.ollama.ollama_bridge import MemoryHandler, call_ollama_api

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test Ollama with Engram memory functions")
    parser.add_argument("--model", type=str, default="llama3:8b", help="Ollama model to use")
    parser.add_argument("--client-id", type=str, default="ollama-test", help="Engram client ID")
    parser.add_argument("--memory-functions", action="store_true", help="Enable memory function detection")
    parser.add_argument("--message", type=str, default="Tell me briefly about persistent memory in AI systems. Add a memory about this conversation.", 
                        help="Message to send to the model")
    return parser.parse_args()

def run_test():
    """Run a non-interactive test of Ollama with Engram memory functions"""
    args = parse_args()
    
    # Set client ID for Engram
    os.environ["ENGRAM_CLIENT_ID"] = args.client_id
    
    print(f"\n=== Testing Ollama with Engram Memory ===")
    print(f"Model: {args.model}")
    print(f"Client ID: {args.client_id}")
    print(f"Memory Functions: {args.memory_functions}")
    
    # Create memory handler
    memory = MemoryHandler()
    
    # Create system prompt
    system_prompt = """You are a helpful assistant with access to a memory system.
To use this system, include special commands in your responses:

- To store information: REMEMBER: {information to remember}
- To search for information: SEARCH: {search term}
- To retrieve recent memories: RETRIEVE: {number of memories}
- To get context-relevant memories: CONTEXT: {context description}
- To find semantically similar memories: SEMANTIC: {query}

Your memory commands will be processed automatically. Be sure to format your memory commands exactly as shown.
Always place memory commands on their own line to ensure they are processed correctly.

This is a test of the memory system. Please demonstrate the memory system by including a REMEMBER: command in your response.
"""
    
    # Create chat history
    chat_history = [
        {"role": "user", "content": args.message}
    ]
    
    # Call Ollama API
    print(f"\nSending message to {args.model}: {args.message}")
    response = call_ollama_api(
        model=args.model,
        messages=chat_history,
        system=system_prompt,
        temperature=0.7
    )
    
    if "error" in response:
        print(f"Error: {response['error']}")
        return
    
    # Get assistant response
    assistant_message = response.get("message", {}).get("content", "")
    if not assistant_message:
        print("Error: No response from model")
        return
    
    print(f"\nResponse from {args.model}:\n{assistant_message}")
    
    # Check for memory operations
    if args.memory_functions:
        print("\nChecking for memory operations...")
        cleaned_message, memory_ops = memory.detect_memory_operations(assistant_message)
        
        if memory_ops:
            print("\nMemory operations detected:")
            for op in memory_ops:
                op_type = op.get("type", "")
                op_input = op.get("input", "")
                print(f"- {op_type.capitalize()}: {op_input}")
                
                # If this is a store operation, display the result
                if op_type == "store":
                    print(f"  Successfully stored memory")
                
                # If this is a search/retrieve operation, display results
                elif op_type in ["search", "retrieve", "context", "semantic"]:
                    results = op.get("result", [])
                    if results:
                        print(f"  Results:")
                        for i, result in enumerate(results[:3]):
                            content = result.get("content", "")
                            if content:
                                print(f"    {i+1}. {content[:80]}...")
                    else:
                        print("  No results found")
            
            print(f"\nCleaned message:\n{cleaned_message}")
        else:
            print("No memory operations detected")
    
    # Verify memory storage by retrieving recent memories
    print("\nRetrieving recent memories:")
    recent_memories = memory.get_recent_memories(3)
    if recent_memories:
        for i, mem in enumerate(recent_memories):
            content = mem.get("content", "")
            if content:
                print(f"{i+1}. {content}")
    else:
        print("No memories found")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    run_test()