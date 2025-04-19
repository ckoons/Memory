#!/usr/bin/env python3
"""
Claude Memory Bridge Example

This script demonstrates how to use the Memory Bridge with Claude.
"""

import os
import sys

# Add project root to Python path to find the module
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.insert(0, project_root)

from engram.cli.claude_helper import (
    check_health, 
    query_memory, 
    store_memory, 
    store_thinking, 
    store_longterm,
    get_context
)

# Import the quickmem module for the simplified interface
from engram.cli.quickmem import (
    mem, think, remember, write, load, 
    compartment, keep, correct,
    # Short aliases
    m, t, r, w, l, c, k, cx
)

def main():
    """Run a demo showing how to use Engram Memory."""
    print("Engram Memory Example\n")
    
    # Check if the memory service is running
    health = check_health()
    if health.get("status") != "ok":
        print("Error: Engram Memory service is not running.")
        print("Please start the memory service with: engram_consolidated")
        return
    
    print(f"Connected to Engram Memory (Client ID: {health.get('client_id')})\n")
    
    # Query existing memories
    print("Checking what I already know about Python...")
    memories = query_memory("Python programming", limit=3)
    
    # Store some new memories in different namespaces
    print("\nLet me remember some facts about Python...")
    
    # Store in conversations namespace
    store_memory(
        "python", 
        "Python is a high-level, interpreted programming language created by Guido van Rossum."
    )
    
    # Store in thinking namespace
    store_thinking(
        "I notice that users who know Python often prefer clear, readable code over " +
        "clever one-liners. This aligns with Python's philosophy of readability."
    )
    
    # Store in longterm namespace
    store_longterm(
        "Python's zen philosophy includes 'Explicit is better than implicit' and " +
        "'Simple is better than complex'."
    )
    
    # Get context for a query
    print("\nGetting memory context for 'Python programming style'...")
    context = get_context("Python programming style")
    
    print("\nHere's how I would use this context in a conversation:")
    print("\n---\n")
    
    # Simulate using the context in a response
    user_query = "What do you know about Python programming style?"
    print(f"User: {user_query}\n")
    
    # This is where Claude would use the context to generate a response
    print("Claude: Based on what I've learned, Python programming emphasizes readability and clarity. ")
    print("The Python philosophy includes principles like 'Explicit is better than implicit' and ")
    print("'Simple is better than complex'. I've noticed that Python developers tend to prefer ")
    print("clear, readable code over clever one-liners, which aligns with Python's overall design philosophy.")
    
    print("\n---\n")
    
    # Demonstrate the session write/load cycle
    print("Demonstrating session memory write/load cycle...")
    
    # Write to session memory
    print("\nWriting to session memory...")
    write("Python is my favorite programming language because of its readability and extensive libraries.")
    
    # Load from session memory
    print("\nLoading from session memory...")
    session_memories = load()
    
    print("\nSimulating a new conversation session:")
    print("\n---\n")
    
    print("User: What programming language do I like best and why?\n")
    
    print("Claude: Let me check my previous session memory...")
    print("[Claude loads previous session context with load()]")
    print("\nBased on our previous conversation, you mentioned that Python is your favorite")
    print("programming language because of its readability and extensive libraries.")
    
    print("\n---\n")
    
    # Demonstrate compartment usage
    print("Demonstrating compartment memory...")
    print("\nCreating and storing in a 'Languages' compartment...")
    compartment("Languages: Python is a high-level language known for readability. JavaScript is widely used for web development.")
    
    # Demonstrate correction
    print("\nDemonstrating memory correction...")
    print("Storing incorrect information...")
    remember("Python was created in 1995.")
    print("\nCorrecting the information...")
    correct("Python was created in 1995.", "Python was created in 1991 by Guido van Rossum.")
    
    print("\n---\n")
    print("Memory bridge example completed successfully!")

if __name__ == "__main__":
    main()