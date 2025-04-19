#!/usr/bin/env python3
"""
Multi-Client Example for Engram

This example demonstrates how to use the Engram API with multiple client IDs.
"""

import asyncio
import httpx
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Engram server URL
SERVER_URL = "http://localhost:8000"

async def store_memory(client_id: str, content: str, namespace: str = "conversations") -> Dict:
    """Store a memory with a specific client ID."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVER_URL}/memory/store",
            headers={"X-Client-ID": client_id},
            json={
                "key": f"memory_{int(datetime.now().timestamp())}",
                "value": content,
                "namespace": namespace
            }
        )
        return response.json()

async def query_memories(client_id: str, query: str, namespace: str = "conversations", limit: int = 5) -> Dict:
    """Query memories for a specific client ID."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SERVER_URL}/memory/query",
            headers={"X-Client-ID": client_id},
            json={
                "query": query,
                "namespace": namespace,
                "limit": limit
            }
        )
        return response.json()

async def get_client_list() -> Dict:
    """Get list of all active clients."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVER_URL}/clients/list")
        return response.json()

async def check_health(client_id: str = None) -> Dict:
    """Check health of the Engram server for a specific client ID."""
    headers = {}
    if client_id:
        headers["X-Client-ID"] = client_id
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVER_URL}/health", headers=headers)
        return response.json()

async def main():
    """Main function to demonstrate multi-client usage."""
    print("=== Engram Multi-Client Example ===")
    
    # Check if server is running
    try:
        health = await check_health()
        print(f"Server status: {health['status']}")
        print(f"Default client: {health['client_id']}")
        print(f"Multi-client support: {'Yes' if health.get('multi_client', False) else 'No'}")
        print()
    except Exception as e:
        print(f"Error connecting to Engram server: {e}")
        print("Make sure the server is running with:")
        print("  ./engram_consolidated --background")
        return
    
    # Define client IDs
    client_ids = ["claude-alpha", "claude-beta", "claude-gamma"]
    
    # Store memories for each client
    print("Storing memories for each client...")
    for client_id in client_ids:
        # Store personal memories
        await store_memory(
            client_id,
            f"I am the {client_id} instance specialized in analysis.",
            "personal"
        )
        
        # Store project memories
        await store_memory(
            client_id,
            f"Project {client_id}: Working on data analysis for 2024 Q2.",
            "projects"
        )
        
        # Store conversation memories
        await store_memory(
            client_id,
            f"User: What are you working on? {client_id}: I'm analyzing the latest data.",
            "conversations"
        )
    
    # Get client list
    print("\nActive clients:")
    clients = await get_client_list()
    for client in clients["clients"]:
        print(f"- {client['client_id']} (last active: {client['last_access_time']})")
    
    # Query memories for each client
    print("\nQuerying memories for each client...")
    for client_id in client_ids:
        print(f"\nResults for {client_id}:")
        
        # Search for "analysis" in all client memories
        results = await query_memories(client_id, "analysis")
        
        # Print the matches
        if "matches" in results and results["matches"]:
            for i, match in enumerate(results["matches"], 1):
                print(f"  {i}. {match.get('content', '')[:80]}...")
        else:
            print("  No matches found")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())