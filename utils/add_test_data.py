#\!/usr/bin/env python3
"""
Add test data to Claude Memory Bridge for visualization demo.
"""

import urllib.request
import urllib.parse
import json
import time

def safe_string(text):
    """URL-encode a string to make it safe for GET requests."""
    return urllib.parse.quote_plus(str(text))

def query_http_api(endpoint, params=None):
    """Query the HTTP API wrapper."""
    base_url = "http://localhost:8001"
    url = f"{base_url}/{endpoint}"
    
    if params:
        param_strings = []
        for key, value in params.items():
            if isinstance(value, dict) or isinstance(value, list):
                param_strings.append(f"{key}={safe_string(json.dumps(value))}")
            else:
                param_strings.append(f"{key}={safe_string(value)}")
        
        url = f"{url}?{'&'.join(param_strings)}"
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error querying API: {e}")
        return {"success": False, "error": str(e)}

def add_test_data():
    """Add test data to memory bridge."""
    print("Adding test data to Claude Memory Bridge...")
    
    # Add conversation memories
    conversations = [
        "The user prefers Python for most programming tasks.",
        "The user is working on a project called ClaudeMemoryBridge.",
        "The user likes to organize code in a modular way.",
        "The user mentioned their cat is named Whiskers.",
        "The user prefers dark mode in their code editor."
    ]
    
    for memory in conversations:
        result = query_http_api("store", {"key": "conversation", "value": memory, "namespace": "conversations"})
        if result.get("success"):
            print(f"Added conversation: {memory}")
        time.sleep(0.2)  # Avoid overwhelming the API
    
    # Add thinking memories
    thinking = [
        "The user seems to value well-organized documentation.",
        "The user appears to be interested in AI memory systems.",
        "The user appreciates detailed explanations about code.",
        "The user likes solutions that are flexible and extensible.",
        "The user values code that handles edge cases gracefully."
    ]
    
    for thought in thinking:
        result = query_http_api("thinking", {"thought": thought})
        if result.get("success"):
            print(f"Added thought: {thought}")
        time.sleep(0.2)
    
    # Add longterm memories
    longterm = [
        "The user is Casey Koons, working on AI memory projects.",
        "Casey prefers clear documentation with examples.",
        "Casey likes tools that are simple yet powerful.",
        "Casey is interested in vector-based memory systems.",
        "Casey values backward compatibility in software."
    ]
    
    for info in longterm:
        result = query_http_api("longterm", {"info": info})
        if result.get("success"):
            print(f"Added longterm memory: {info}")
        time.sleep(0.2)
    
    # Create and populate compartments
    compartments = {
        "Project": "This is the main project compartment for ClaudeMemoryBridge.",
        "Project.Architecture": "ClaudeMemoryBridge uses a modular architecture with core, API, and CLI components.",
        "Project.Features": "ClaudeMemoryBridge supports memory compartmentalization, session persistence, and memory expiration.",
        "Personal": "Casey is working on AI memory projects.",
        "Personal.Preferences": "Casey prefers Python, clear documentation, and well-organized code."
    }
    
    for name, content in compartments.items():
        # Create compartment
        result = query_http_api("compartment/create", {"name": name})
        if result.get("success"):
            compartment_id = result.get("compartment_id")
            print(f"Created compartment: {name} (ID: {compartment_id})")
            
            # Store content in compartment
            store_result = query_http_api("compartment/store", {"compartment": compartment_id, "content": content})
            if store_result.get("success"):
                print(f"  - Added content to compartment")
            
            # Activate the compartment
            activate_result = query_http_api("compartment/activate", {"compartment": compartment_id})
            if activate_result.get("success"):
                print(f"  - Activated compartment")
        time.sleep(0.2)
    
    # Add session memories
    session = [
        "Today we worked on implementing the memory visualization web UI.",
        "We addressed NumPy 2.x compatibility issues.",
        "We created a simplified web UI for environments with dependency issues."
    ]
    
    for note in session:
        result = query_http_api("write", {"content": note})
        if result.get("success"):
            print(f"Added session memory: {note}")
        time.sleep(0.2)
    
    print("All test data added successfully\!")

if __name__ == "__main__":
    add_test_data()
