#!/usr/bin/env python3
"""
Hybrid AI System with Claude as Memory Manager

This script implements a hybrid architecture where Claude acts as a memory manager
for Llama/Echo, leveraging Claude's strengths in reasoning and memory organization.
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
import json
from pathlib import Path
import requests

# Import Engram memory functions
try:
    from engram.cli.quickmem import m, k, run, s, c, v
except ImportError:
    print("Error importing Engram memory functions")
    sys.exit(1)

# Ollama API settings
OLLAMA_API_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_URL = f"{OLLAMA_API_HOST}/api/chat"

# Standard memory tags
CLAUDE_TO_ECHO = "CLAUDE_TO_ECHO"
ECHO_TO_CLAUDE = "ECHO_TO_CLAUDE"
MEMORY_REQUEST = "MEMORY_REQUEST"
MEMORY_RESPONSE = "MEMORY_RESPONSE"

def call_ollama_api(model, messages, system=None, temperature=0.7):
    """Call the Ollama API with the given parameters."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": 0.9,
            "num_predict": 2048
        }
    }
    
    if system:
        payload["system"] = system
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama API: {e}")
        return {"error": str(e)}

async def process_memory_request(query):
    """Have Claude process a memory request from Echo."""
    # Set Engram client ID for Claude
    os.environ["ENGRAM_CLIENT_ID"] = "claude"
    
    print(f"Processing memory request: {query}")
    
    # Search for relevant memories
    semantic_results = await v(query)
    keyword_results = await k(query)
    context_results = await c(query)
    
    # Combine and deduplicate results
    all_results = semantic_results + keyword_results + context_results
    seen_ids = set()
    unique_results = []
    
    for result in all_results:
        result_id = result.get("id")
        if result_id and result_id not in seen_ids:
            seen_ids.add(result_id)
            unique_results.append(result)
    
    # Format the results
    if unique_results:
        memory_response = f"Memory search results for: '{query}'\n\n"
        for i, result in enumerate(unique_results[:5]):
            content = result.get("content", "")
            memory_response += f"{i+1}. {content}\n\n"
    else:
        memory_response = f"No memories found for: '{query}'"
    
    # Store the response for Echo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await m(f"{MEMORY_RESPONSE}: [{timestamp}] {memory_response}")
    
    return memory_response

async def get_memory_response():
    """Get the latest memory response for Echo."""
    responses = await k(MEMORY_RESPONSE)
    if responses:
        return responses[0].get("content", "").split("] ", 1)[1]
    return "No memory response found."

async def hybrid_chat(model="llama3:8b", interactive=True):
    """Run a hybrid chat with Echo as the primary model and Claude as memory manager."""
    # Set Engram client ID for Echo
    os.environ["ENGRAM_CLIENT_ID"] = "ollama"
    
    # Check if Ollama is running
    try:
        response = requests.get(f"{OLLAMA_API_HOST}/api/tags")
        if response.status_code != 200:
            print(f"Error connecting to Ollama: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Ollama is not running. Please start Ollama first.")
        sys.exit(1)
    
    # Set up system prompt for the hybrid mode
    system_prompt = """You are Echo, an AI assistant powered by Llama. You have access to a memory system managed by Claude.

To access your memory system, include special commands in your responses:

1. To store information:
   REMEMBER: information to remember

2. To search for information:
   SEARCH: search term

When you use these commands, Claude will process them and provide relevant information from your memory.

You can also communicate directly with Claude using:
CLAUDE: your message here

Your memory commands will be processed automatically and removed from your visible response."""
    
    # Set up chat history
    chat_history = []
    
    print(f"\nHybrid AI System (Echo powered by {model} with Claude as memory manager)")
    print("Type 'exit' to quit, 'reset' to reset chat history\n")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ")
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit']:
                break
            elif user_input.lower() == 'reset':
                chat_history = []
                print("Chat history reset.")
                continue
            
            # Add user message to chat history
            chat_history.append({"role": "user", "content": user_input})
            
            # Call Ollama API
            response = call_ollama_api(
                model=model,
                messages=chat_history,
                system=system_prompt,
                temperature=0.7
            )
            
            if "error" in response:
                print(f"Error: {response['error']}")
                continue
        
            # Get assistant response
            assistant_message = response.get("message", {}).get("content", "")
            if not assistant_message:
                print("Error: No response from model")
                continue
            
            # Process memory operations
            cleaned_message = assistant_message
            memory_requests = []
            
            # Check for REMEMBER command
            if "REMEMBER:" in assistant_message:
                remember_parts = assistant_message.split("REMEMBER:")
                for i in range(1, len(remember_parts)):
                    memory_text = remember_parts[i].split("\n", 1)[0].strip()
                    if memory_text:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        await m(f"Echo memory: [{timestamp}] {memory_text}")
                        print(f"\n[Memory system: Remembered '{memory_text}']")
                
                # Remove REMEMBER command from response
                cleaned_message = assistant_message.replace("REMEMBER:", "REMEMBERED:")
            
            # Check for SEARCH command
            if "SEARCH:" in assistant_message:
                search_parts = assistant_message.split("SEARCH:")
                for i in range(1, len(search_parts)):
                    query = search_parts[i].split("\n", 1)[0].strip()
                    if query:
                        memory_requests.append(query)
                        
                        # Have Claude process the memory request
                        memory_response = await process_memory_request(query)
                        print(f"\n[Memory system: Processed search for '{query}']")
                        print(f"Claude's response: {memory_response[:100]}...")
                
                # Remove SEARCH command from response
                cleaned_message = cleaned_message.replace("SEARCH:", "SEARCHED:")
            
            # Check for direct message to Claude
            if "CLAUDE:" in assistant_message:
                claude_parts = assistant_message.split("CLAUDE:")
                for i in range(1, len(claude_parts)):
                    message = claude_parts[i].split("\n", 1)[0].strip()
                    if message:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        await m(f"{ECHO_TO_CLAUDE}: [{timestamp}] {message}")
                        print(f"\n[Message sent to Claude: '{message}']")
                
                # Remove CLAUDE command from response
                cleaned_message = cleaned_message.replace("CLAUDE:", "TO CLAUDE:")
            
            # Display the cleaned response
            print(f"\n{model}: {cleaned_message}")
            
            # Add assistant message to chat history
            chat_history.append({"role": "assistant", "content": cleaned_message})
            
            # Check for messages from Claude
            claude_messages = await k(CLAUDE_TO_ECHO)
            if claude_messages:
                newest_message = claude_messages[0]
                content = newest_message.get("content", "")
                try:
                    # Extract the actual message (after timestamp)
                    msg = content.split("] ", 1)[1]
                    print(f"\n[Message from Claude: {msg}]")
                except:
                    print(f"\n[Message from Claude: {content}]")
            
            # Check for memory responses if there were requests
            if memory_requests:
                memory_response = await get_memory_response()
                print(f"\n[Memory system response: {memory_response[:150]}...]")
                
                # Add Claude's memory response to chat history
                memory_prompt = f"\nBased on your memory search, Claude found the following information:\n\n{memory_response}\n\nPlease incorporate this information into your next response."
                chat_history.append({"role": "user", "content": memory_prompt})
                
        except EOFError:
            print("\nDetected EOF. Exiting...")
            break
        except KeyboardInterrupt:
            print("\nExiting due to user interrupt")
            break
        except Exception as e:
            print(f"Error in hybrid chat: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Hybrid AI System")
    parser.add_argument("--model", type=str, default="llama3:8b", 
                        help="Ollama model to use (default: llama3:8b)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Temperature for model generation (0.0-1.0)")
    
    args = parser.parse_args()
    
    try:
        run(hybrid_chat(model=args.model))
    except Exception as e:
        print(f"Error in hybrid system: {e}")

if __name__ == "__main__":
    main()