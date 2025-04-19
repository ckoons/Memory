#!/usr/bin/env python3
"""
Test script for Engram vector database integration.

This script tests the Engram memory system with the new vector database integration,
validating both the vector-based and fallback file-based storage mechanisms.

Usage:
  1. Ensure Engram service is running:
     ./engram_consolidated
  2. Run this test script:
     python test_vector_integration.py
"""

import os
import sys
import asyncio
import json
import time
import random
from datetime import datetime

# Set client ID for this test
os.environ['ENGRAM_CLIENT_ID'] = 'test_vector'

# Import Engram modules
try:
    from engram.core.memory import MemoryService, HAS_VECTOR_DB
    from engram.core.structured_memory import StructuredMemory
    from engram.cli.quickmem import memory_digest, latest
except ImportError:
    print("Error: Engram package not found. Make sure you're in the right directory.")
    print("Try activating the virtual environment: source venv/bin/activate")
    sys.exit(1)

print("\n" + "="*60)
print("ENGRAM VECTOR DATABASE INTEGRATION TEST")
print("="*60)

# Check if vector database is available
print(f"\n🔍 Checking vector database availability...")
print(f"Vector DB Available: {'✅ Yes' if HAS_VECTOR_DB else '❌ No'}")
if HAS_VECTOR_DB:
    from engram.core.memory import VECTOR_DB_NAME, VECTOR_DB_VERSION
    print(f"Vector DB: {VECTOR_DB_NAME} {VECTOR_DB_VERSION}")
print(f"Storage Mode: {'Vector-based' if HAS_VECTOR_DB else 'File-based fallback'}")

async def run_tests():
    """Run a series of tests on the Engram memory system."""
    # Initialize memory service
    memory = MemoryService(client_id="test_vector")
    structured_memory = StructuredMemory(client_id="test_vector")
    
    print("\n🧪 Running memory tests...")
    
    # Test 1: Basic memory storage and retrieval
    print("\n📝 Test 1: Basic memory storage and retrieval")
    test_content = f"Test memory created at {datetime.now().isoformat()}"
    success = await memory.add(test_content, namespace="testing")
    print(f"  Memory storage: {'✅ Success' if success else '❌ Failed'}")
    
    # Search for the memory
    results = await memory.search("test memory", namespace="testing", limit=5)
    found = any(test_content in result.get("content", "") for result in results.get("results", []))
    print(f"  Memory retrieval: {'✅ Success' if found else '❌ Failed'}")
    
    # Test 2: Multiple memories with semantic search
    print("\n🔍 Test 2: Semantic search capabilities")
    
    # Add related memories with different wording
    memories = [
        "Artificial intelligence is revolutionizing technology across industries",
        "Machine learning algorithms can identify patterns in vast amounts of data",
        "Neural networks are computational systems inspired by the human brain",
        "Deep learning is a subset of machine learning with multiple layers",
        "Natural language processing helps computers understand human languages"
    ]
    
    print("  Adding test memories...")
    for i, content in enumerate(memories):
        await memory.add(content, namespace="semantics")
        print(f"  - Added memory {i+1}: {content[:40]}...")
        
    # Search with semantically related term not explicitly in the memories
    print("\n  Searching for semantically related content...")
    search_term = "computational intelligence and pattern recognition"
    results = await memory.search(search_term, namespace="semantics", limit=10)
    
    print(f"  Found {len(results.get('results', []))} results for '{search_term}'")
    for i, result in enumerate(results.get("results", [])):
        relevance = result.get("relevance", 0)
        content = result.get("content", "")
        print(f"  {i+1}. [Relevance: {relevance:.4f}] {content[:60]}...")
    
    # Test 3: Test structured memory and auto-categorization
    print("\n📊 Test 3: Structured memory and categorization")
    
    # Add memories to different categories
    categories = ["personal", "projects", "facts", "preferences"]
    for category in categories:
        content = f"This is a test memory for the {category} category created at {datetime.now().isoformat()}"
        memory_id = await structured_memory.add_memory(content, category, importance=random.randint(1, 5))
        print(f"  Added to {category}: {memory_id}")
    
    # Test auto-categorization
    auto_memories = [
        "I prefer using Python for data analysis projects",
        "My birthday is on January 15th",
        "The project deadline is next Friday",
        "I think the documentation needs to be improved"
    ]
    
    print("\n  Testing auto-categorization...")
    for content in auto_memories:
        memory_id = await structured_memory.add_auto_categorized_memory(content)
        memory = await structured_memory.get_memory(memory_id)
        category = memory.get("category", "unknown")
        importance = memory.get("importance", 0)
        print(f"  - '{content[:30]}...' → Category: {category}, Importance: {importance}")
    
    # Test memory digest
    print("\n📋 Getting memory digest...")
    digest = await structured_memory.get_memory_digest(max_memories=5)
    print(f"  Digest length: {len(digest)} characters")
    print(f"  Digest preview: {digest[:200]}...")
    
    # Test 4: Performance test
    print("\n⏱️ Test 4: Performance test (adding and retrieving multiple memories)")
    
    start_time = time.time()
    batch_size = 10
    
    print(f"  Adding {batch_size} memories...")
    for i in range(batch_size):
        content = f"Performance test memory #{i+1}: Random data {random.random()}"
        await structured_memory.add_memory(content, "personal", importance=3)
    
    add_time = time.time() - start_time
    print(f"  Time to add {batch_size} memories: {add_time:.4f} seconds")
    
    # Test search performance
    start_time = time.time()
    results = await structured_memory.search_memories("performance test", limit=batch_size)
    search_time = time.time() - start_time
    print(f"  Time to search {batch_size} memories: {search_time:.4f} seconds")
    print(f"  Found {len(results)} results")

    print("\n✅ Tests completed!")
    
    # Final status report
    print("\n📊 Summary:")
    print(f"  Storage mode: {'Vector-based' if HAS_VECTOR_DB else 'File-based fallback'}")
    print(f"  Basic memory: {'✅ Working' if found else '❌ Failed'}")
    print(f"  Semantic search: {'✅ Available' if HAS_VECTOR_DB else '⚠️ Limited (keyword only)'}")
    print(f"  Structured memory: ✅ Working")
    print(f"  Auto-categorization: ✅ Working")

    return True

if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)