#!/usr/bin/env python3
"""
Standardized System Prompts for Ollama Models

This module provides standardized system prompts for different Ollama models to enable
consistent communication capabilities across all AI instances in the Engram network.
"""

import os
import sys
from typing import Dict, Optional, List

# Default memory command patterns that all models should support
DEFAULT_MEMORY_COMMANDS = {
    "REMEMBER": "Store information in memory",
    "SEARCH": "Find information in memory by keyword",
    "RETRIEVE": "Get recent memories (specify number)",
    "CONTEXT": "Get memories relevant to a specific context",
    "SEMANTIC": "Find semantically similar memories",
    "FORGET": "Mark information to be forgotten"
}

# Advanced commands that may not be supported by all models
ADVANCED_MEMORY_COMMANDS = {
    "LIST": "Show recent memory entries",
    "SUMMARIZE": "Create a summary of memories on a topic",
    "TAG": "Add tags to memories for better organization",
    "PRIORITY": "Set priority level for a memory"
}

# Communication-specific commands for AI-to-AI interaction
COMMUNICATION_COMMANDS = {
    "SEND": "Send a message to another AI model",
    "CHECK": "Check for messages from other models",
    "REPLY": "Reply to a specific message",
    "BROADCAST": "Send a message to all available models"
}

# Known Ollama models and their capabilities
MODEL_CAPABILITIES = {
    "llama3": {
        "memory_cmds": list(DEFAULT_MEMORY_COMMANDS.keys()) + ["LIST", "SUMMARIZE"],
        "comm_cmds": ["SEND", "CHECK", "REPLY"],
        "supports_vector": True,
        "persona": "Echo"
    },
    "mistral": {
        "memory_cmds": list(DEFAULT_MEMORY_COMMANDS.keys()),
        "comm_cmds": ["SEND", "CHECK"],
        "supports_vector": False,
        "persona": "Mist"
    },
    "mixtral": {
        "memory_cmds": list(DEFAULT_MEMORY_COMMANDS.keys()) + ["LIST", "SUMMARIZE", "TAG"],
        "comm_cmds": ["SEND", "CHECK", "REPLY", "BROADCAST"],
        "supports_vector": True,
        "persona": "Mix"
    },
    "phi3": {
        "memory_cmds": list(DEFAULT_MEMORY_COMMANDS.keys()),
        "comm_cmds": ["SEND", "CHECK"],
        "supports_vector": False,
        "persona": "Phi"
    },
    "default": {
        "memory_cmds": list(DEFAULT_MEMORY_COMMANDS.keys()),
        "comm_cmds": ["SEND", "CHECK"],
        "supports_vector": False,
        "persona": "Echo"
    }
}

def get_model_capabilities(model_name: str) -> Dict:
    """Get capabilities for a specific model."""
    # Extract the base model name from the full model string (e.g., llama3:8b -> llama3)
    base_model = model_name.split(':')[0].lower()
    
    # Match the base model to known models
    for known_model in MODEL_CAPABILITIES:
        if known_model in base_model:
            return MODEL_CAPABILITIES[known_model]
    
    # Return default capabilities if no match found
    return MODEL_CAPABILITIES["default"]

def get_memory_system_prompt(model_name: str) -> str:
    """
    Generate a system prompt for a specific model that explains memory capabilities.
    
    Args:
        model_name: The name of the Ollama model
        
    Returns:
        String containing the system prompt
    """
    capabilities = get_model_capabilities(model_name)
    memory_commands = capabilities["memory_cmds"]
    supports_vector = capabilities["supports_vector"]
    
    # Start with a basic introduction
    prompt = f"""You have access to Engram, a memory system that can store and retrieve information.
To use this system, include special commands in your responses:

"""
    
    # Add memory commands based on model's capabilities
    for cmd in memory_commands:
        if cmd in DEFAULT_MEMORY_COMMANDS:
            prompt += f"- To {DEFAULT_MEMORY_COMMANDS[cmd]}: {cmd}: {{information}}\n"
        elif cmd in ADVANCED_MEMORY_COMMANDS:
            prompt += f"- To {ADVANCED_MEMORY_COMMANDS[cmd]}: {cmd}: {{information}}\n"
            
    # Add information about vector search if supported
    if supports_vector:
        prompt += "\nYou have access to semantic vector search capabilities for finding similar concepts.\n"
    
    # Add formatting instructions
    prompt += """
Your memory commands will be processed automatically. The command format is flexible:
- Standard format: REMEMBER: information
- Markdown format: **REMEMBER**: information
- With or without colons: REMEMBER information

Always place memory commands on their own line to ensure they are processed correctly.
When you use these commands, they will be processed and removed from your visible response.
"""

    return prompt

def get_communication_system_prompt(model_name: str, available_models: Optional[List[str]] = None) -> str:
    """
    Generate a system prompt for a specific model that explains communication capabilities.
    
    Args:
        model_name: The name of the Ollama model
        available_models: Optional list of other AI models available for communication
        
    Returns:
        String containing the system prompt
    """
    capabilities = get_model_capabilities(model_name)
    comm_commands = capabilities["comm_cmds"]
    persona = capabilities["persona"]
    
    # Default available models if none provided
    if not available_models:
        available_models = ["Claude"]
    
    # Start with a basic introduction
    prompt = f"""You are {persona}, an AI assistant with the ability to communicate with other AI models.
Your messages to other AIs are stored in Engram's memory system for asynchronous communication.

To communicate with other AIs, use these commands in your responses:

"""
    
    # Add communication commands based on model's capabilities
    for cmd in comm_commands:
        if cmd == "SEND":
            prompt += f"- To send a message: SEND TO [AI_NAME]: {{message}}\n"
        elif cmd == "CHECK":
            prompt += f"- To check for messages: CHECK MESSAGES FROM [AI_NAME]\n"
        elif cmd == "REPLY":
            prompt += f"- To reply to a message: REPLY TO [AI_NAME]: {{message}}\n"
        elif cmd == "BROADCAST":
            prompt += f"- To broadcast to all AIs: BROADCAST: {{message}}\n"
    
    # Add list of available AIs
    prompt += f"\nAvailable AIs for communication:\n"
    for ai in available_models:
        prompt += f"- {ai}\n"
    
    # Add message format information
    prompt += """
Communication messages use the following format in memory:
TAG: [TIMESTAMP] [Thread: THREAD_ID] TAG:SENDER:RECIPIENT message

Example:
ECHO_TO_CLAUDE: [2025-03-21 12:45:32] [Thread: science] ECHO_TO_CLAUDE:Echo:Claude What's your understanding of quantum mechanics?

Communication commands will be processed automatically and then removed from your visible response.
"""

    return prompt

def get_combined_system_prompt(model_name: str, available_models: Optional[List[str]] = None) -> str:
    """
    Generate a combined system prompt with both memory and communication capabilities.
    
    Args:
        model_name: The name of the Ollama model
        available_models: Optional list of other AI models available for communication
        
    Returns:
        String containing the combined system prompt
    """
    memory_prompt = get_memory_system_prompt(model_name)
    comm_prompt = get_communication_system_prompt(model_name, available_models)
    
    # Get the persona from capabilities
    persona = get_model_capabilities(model_name)["persona"]
    
    # Combine the prompts with a unified introduction
    combined = f"""You are {persona}, an AI assistant with access to Engram's memory system and communication network.
You can store information in memory and communicate with other AI models.

=== MEMORY CAPABILITIES ===
{memory_prompt}

=== COMMUNICATION CAPABILITIES ===
{comm_prompt}

Remember that you have a distinct identity as {persona} when communicating with other AI models.
Your communications should reflect your unique perspective and capabilities.
"""

    return combined

if __name__ == "__main__":
    # Simple CLI tool to generate system prompts
    if len(sys.argv) < 2:
        print("Usage: python ollama_system_prompts.py <model_name> [memory|communication|combined]")
        sys.exit(1)
    
    model_name = sys.argv[1]
    prompt_type = sys.argv[2] if len(sys.argv) > 2 else "combined"
    
    if prompt_type == "memory":
        print(get_memory_system_prompt(model_name))
    elif prompt_type == "communication":
        print(get_communication_system_prompt(model_name))
    else:  # default to combined
        print(get_combined_system_prompt(model_name))