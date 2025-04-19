#!/usr/bin/env python3
"""
Ollama Bridge for Engram Memory
This script creates a bridge between Ollama and Engram, allowing Ollama models
to use Engram's memory system.

This module has been refactored into a more modular structure.
It now serves as a compatibility layer that imports from the new structure.
"""

import os
import sys
import time
import argparse
import json
import asyncio
import re
from typing import List, Dict, Any, Optional
import requests

# Ensure the bridge package is in the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import from refactored structure
from bridge.cli.args import parse_args, display_args
from bridge.cli.commands import process_special_command, display_help
from bridge.api.client import call_ollama_api, check_ollama_status, pull_model
from bridge.api.models import get_system_prompt
from bridge.memory.handler import MemoryHandler, MEMORY_AVAILABLE
from bridge.memory.operations import detect_memory_operations, format_memory_operations_report
from bridge.communication.messenger import Messenger, detect_communication_operations, format_communication_operations_report
from bridge.communication.dialog import DialogManager, detect_dialog_operations
from bridge.utils.helpers import colorize, print_colored, set_environment_variables, format_chat_message, should_save_to_memory, format_memory_for_saving
from bridge.utils.pattern_matching import detect_all_operations, format_operations_report

def main():
    """Main function for the Ollama bridge."""
    # Parse command line arguments
    args = parse_args()
    
    # Set environment variables
    set_environment_variables(args)
    
    # Create memory handler
    memory = MemoryHandler(client_id=args.client_id, use_hermes=args.hermes_integration)
    
    # Make it globally available for error recovery
    global memory_handler
    memory_handler = memory
    
    # Create dialog manager
    dialog_manager = DialogManager(client_id=args.client_id)
    
    # Create messenger
    messenger = Messenger(client_id=args.client_id)
    
    # Set up system prompt
    args.system = get_system_prompt(
        args.model, 
        args.prompt_type, 
        args.available_models, 
        args.system
    )
    
    if args.system:
        prompt_type_display = args.prompt_type if args.system != args.prompt_type else "custom"
        print(f"Using {prompt_type_display} system prompt for {args.model}")
    
    # Check if Ollama is running
    ollama_status = check_ollama_status()
    if ollama_status["status"] != "ok":
        print("Error: Ollama is not running. Please start Ollama first.")
        sys.exit(1)
    
    # Check if model is available
    available_models = ollama_status["models"]
    if args.model not in available_models:
        print(f"Warning: Model '{args.model}' not found in available models.")
        print(f"Available models: {', '.join(available_models)}")
        proceed = input("Do you want to pull this model now? (y/n): ")
        if proceed.lower() == 'y':
            print(f"Pulling model {args.model}...")
            pull_result = pull_model(args.model)
            if pull_result["status"] != "ok":
                print(f"Error pulling model: {pull_result.get('code', 'unknown')}")
                sys.exit(1)
            print(f"Model {args.model} pulled successfully!")
        else:
            print("Please choose an available model or pull the requested model first.")
            sys.exit(1)
    
    # Check if memory service is running
    if MEMORY_AVAILABLE:
        status = memory.check_memory_status()
        print(f"Memory service status: {status.get('status', 'unknown')}")
    
    # Print welcome message
    display_args(args)
    
    # Initialize chat history
    chat_history = []
    
    if MEMORY_AVAILABLE:
        # Load most recent memories
        try:
            print("Recent memories:")
            recent_memories = memory.get_recent_memories(5)
            if recent_memories:
                for mem in recent_memories:
                    content = mem.get("content", "")
                    if content:
                        print(f"- {content[:80]}...")
                
                try:
                    use_recent = input("Include recent memories in conversation? (y/n): ")
                    if use_recent.lower() == 'y':
                        # Add memories to system prompt
                        memory_text = "Here are some recent memories that might be relevant:\n"
                        for mem in recent_memories:
                            content = mem.get("content", "")
                            if content:
                                memory_text += f"- {content}\n"
                        
                        if args.system:
                            args.system = args.system + "\n\n" + memory_text
                        else:
                            args.system = memory_text
                except EOFError:
                    print("\nDetected EOF during input. Continuing without recent memories...")
            else:
                print("No recent memories found.")
        except Exception as e:
            print(f"Error loading recent memories: {e}")
    
    # Main chat loop
    while True:
        try:
            # Check for messages in dialog mode
            if dialog_manager.dialog_mode:
                dialog_manager.check_for_messages(
                    args.model, 
                    args.system, 
                    chat_history, 
                    args.temperature, 
                    args.top_p, 
                    args.max_tokens
                )
            
            # Get user input with timeout to support dialog mode
            user_input = dialog_manager.get_user_input_with_timeout()
            
            # If no input in dialog mode, continue the loop
            if user_input is None:
                continue
            
            # Process special commands
            command_processed, message = process_special_command(user_input, memory)
            if command_processed:
                if message:
                    print(message)
                if user_input.lower() in ['exit', '/quit']:
                    break
                continue
                
        except EOFError:
            print("\nDetected EOF. Exiting...")
            break
        
        # Add user message to chat history, optionally enhancing with memory
        if MEMORY_AVAILABLE and args.memory_functions:
            # If using memory functions, enhance with memory
            enhanced_input = memory.enhance_prompt_with_memory(user_input)
            if enhanced_input != user_input:
                print("\n[Memory system: Enhancing prompt with relevant memories]")
                chat_history.append({"role": "user", "content": enhanced_input})
            else:
                chat_history.append({"role": "user", "content": user_input})
        else:
            chat_history.append({"role": "user", "content": user_input})
        
        # Call Ollama API
        response = call_ollama_api(
            model=args.model,
            messages=chat_history,
            system=args.system,
            temperature=args.temperature,
            top_p=args.top_p,
            max_tokens=args.max_tokens
        )
        
        if "error" in response:
            print(f"Error: {response['error']}")
            continue
    
        # Get assistant response
        assistant_message = response.get("message", {}).get("content", "")
        if assistant_message:
            # Check for memory, communication, and dialog operations in response if enabled
            if MEMORY_AVAILABLE and args.memory_functions:
                try:
                    # Create handlers dictionary
                    handlers = {
                        "memory": memory,
                        "messenger": messenger,
                        "dialog": dialog_manager
                    }
                    
                    # Detect all operations
                    cleaned_message, operations = detect_all_operations(assistant_message, handlers)
                    
                    # Format operations report
                    ops_report = format_operations_report(operations)
                    
                    # If operations were detected, print report and use cleaned message
                    if ops_report:
                        print(ops_report)
                    assistant_message = cleaned_message
                
                except Exception as e:
                    print(f"Error processing operations: {e}")
            
            print(f"\n{args.model}: {assistant_message}")
            
            # Add assistant message to chat history
            chat_history.append({"role": "assistant", "content": assistant_message})
            
            # Automatically save significant interactions to memory
            if MEMORY_AVAILABLE and should_save_to_memory(user_input, assistant_message):
                memory_text = format_memory_for_saving(user_input, assistant_message, args.model)
                memory.store_memory(memory_text)
        else:
            print("Error: No response from model")

if __name__ == "__main__":
    main()