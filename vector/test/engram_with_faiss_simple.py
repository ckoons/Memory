#!/usr/bin/env python
"""
Launcher for Engram with Ollama and FAISS-based memory adapter.
This implementation doesn't use SentenceTransformers or other libraries
that have NumPy 2.x compatibility issues.

Usage:
    python engram_with_faiss_simple.py --model llama3:8b
"""

import os
import sys
import logging
import argparse
import importlib.util
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("engram_with_faiss_simple")

# Check if FAISS is available
try:
    import faiss
    import numpy as np
    logger.info(f"FAISS version: {faiss.__version__} found")
    logger.info(f"NumPy version: {np.__version__} found")
except ImportError:
    logger.error("FAISS not found. Please install with: pip install faiss-cpu")
    sys.exit(1)

def find_engram_dir() -> str:
    """Find the Engram directory"""
    # First check if we're in the Engram directory
    if os.path.exists("engram") and os.path.isdir("engram"):
        return os.getcwd()
    
    # Check parent directory
    parent = os.path.dirname(os.getcwd())
    if os.path.exists(os.path.join(parent, "engram")) and os.path.isdir(os.path.join(parent, "engram")):
        return parent
    
    # Otherwise assume we're in a subdirectory of Engram
    return os.path.dirname(os.getcwd())

def mock_system_methods_for_module(module_name: str, mock_methods: Dict[str, Any]) -> None:
    """
    Mock system methods in a module by replacing them with provided implementations.
    This allows us to swap out dependencies without modifying the source code.
    
    Args:
        module_name: The name of the module to modify
        mock_methods: Dictionary mapping method names to mock implementations
    """
    if module_name in sys.modules:
        module = sys.modules[module_name]
        for method_name, mock_impl in mock_methods.items():
            if hasattr(module, method_name):
                setattr(module, method_name, mock_impl)
                logger.info(f"Mocked {module_name}.{method_name}")

def patch_memory_module() -> bool:
    """
    Patch the Engram memory module to use our FAISS-based implementation.
    
    Returns:
        True if patching was successful, False otherwise
    """
    try:
        # First add the Engram directory to the Python path
        engram_dir = find_engram_dir()
        if engram_dir not in sys.path:
            sys.path.insert(0, engram_dir)
        
        # Find our adapter module
        adapter_path = os.path.join(os.path.dirname(__file__), "engram_memory_adapter.py")
        if not os.path.exists(adapter_path):
            logger.error(f"Memory adapter module not found at: {adapter_path}")
            return False
        
        # Import the adapter module
        spec = importlib.util.spec_from_file_location("engram_memory_adapter", adapter_path)
        if not spec or not spec.loader:
            logger.error("Failed to load memory adapter module")
            return False
            
        adapter_module = importlib.util.module_from_spec(spec)
        sys.modules["engram_memory_adapter"] = adapter_module
        spec.loader.exec_module(adapter_module)
        
        # Replace the MemoryService class in engram.core.memory
        memory_module_name = "engram.core.memory"
        
        # Mock a minimal module structure if the module doesn't exist
        if memory_module_name not in sys.modules:
            sys.modules[memory_module_name] = type("MockModule", (), {})
        
        # Replace the MemoryService class
        sys.modules[memory_module_name].MemoryService = adapter_module.MemoryService
        
        logger.info("Successfully patched memory module with FAISS adapter")
        return True
            
    except Exception as e:
        logger.error(f"Failed to patch memory module: {str(e)}")
        return False

def main():
    """Main entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Engram with Ollama and FAISS")
    parser.add_argument("--model", type=str, default="llama3:8b", 
                        help="Ollama model to use (e.g. llama3:8b)")
    parser.add_argument("--prompt", type=str, default="combined",
                        help="Prompt type (e.g. combined, direct)")
    parser.add_argument("--client-id", type=str, default="ollama",
                        help="Client ID for Engram")
    parser.add_argument("--vector-dimension", type=int, default=128,
                        help="Dimension of vector embeddings")
    parser.add_argument("--use-gpu", action="store_true",
                        help="Use GPU for FAISS if available")
    args = parser.parse_args()
    
    # Patch memory module
    if not patch_memory_module():
        logger.error("Failed to apply FAISS patch")
        print("❌ Failed to patch memory module")
        sys.exit(1)
    
    # Import Engram modules that use the patched memory module
    try:
        # Now import the patched Engram modules
        # Correctly import memory functions from ollama_bridge instead since
        # detect_memory_operations doesn't exist in quickmem
        try:
            from engram.ollama.ollama_bridge import detect_memory_operations, handle_memory_operations
        except ImportError:
            # Create placeholder functions if needed
            def detect_memory_operations(text):
                return text, []
                
            def handle_memory_operations(text, client_id="ollama"):
                return text, []
                
        from engram.core.memory import MemoryService
        
        # Initialize memory service with our configuration
        memory_service = MemoryService(
            client_id=args.client_id,
            memory_dir="memories",
            vector_dimension=args.vector_dimension,
            use_gpu=args.use_gpu
        )
        
        print("\n🔄 Successfully patched memory module with FAISS adapter")
        print(f"Starting Ollama bridge with Engram memory (FAISS-enabled)...")
        print(f"Model: {args.model}")
        print(f"Prompt type: {args.prompt}")
        print(f"Client ID: {args.client_id}")
        print(f"Working directory: {os.getcwd()}")
        print("\nType 'exit' or '/quit' to exit\n")
        
        # Get Engram directory 
        engram_dir = find_engram_dir()
        
        # Add command to Engram's path and run the Ollama bridge
        ollama_bridge_path = os.path.join(engram_dir, "ollama", "ollama_bridge.py")
        if not os.path.exists(ollama_bridge_path):
            logger.error(f"Ollama bridge not found at: {ollama_bridge_path}")
            sys.exit(1)
        
        # Create our own implementation calling directly into ollama_bridge functions
        print("\n--- Starting Engram-enabled Ollama chat ---")
        print(f"Model: {args.model}")
        print(f"Client ID: {args.client_id}\n")
        
        # Import required modules
        import requests
        
        # Set up Ollama API and chat history
        OLLAMA_API_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        OLLAMA_API_URL = f"{OLLAMA_API_HOST}/api/chat"
        chat_history = []
        
        # Basic Ollama API function
        def chat_with_ollama(model, messages, system=None, temperature=0.7):
            """Call the Ollama API with the given parameters."""
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature
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
        
        # Main chat loop with improved input handling
        import sys
        import select
        import time
        
        print("\nEnter your messages below. Type 'exit' or '/quit' to quit.")
        print("Press Ctrl+C to interrupt the chat.\n")
        
        # Set up polling for better input handling
        poll_obj = select.poll()
        poll_obj.register(sys.stdin, select.POLLIN)
        
        while True:
            try:
                # Display prompt and flush to ensure it's visible
                sys.stdout.write("\nYou: ")
                sys.stdout.flush()
                
                # Use polling with timeout to avoid blocking indefinitely
                if poll_obj.poll(100):  # 100ms timeout
                    user_input = sys.stdin.readline().strip()
                else:
                    # No input available yet, continue polling
                    time.sleep(0.1)
                    continue
                
                # Check for empty input
                if not user_input:
                    continue
                    
                # Check for exit command
                if user_input.lower() in ["exit", "quit", "/quit", "/exit"]:
                    print("Exiting chat.")
                    break
                
                # Add to chat history
                chat_history.append({"role": "user", "content": user_input})
                
                # Provide feedback that we're processing
                print(f"Processing your request with {args.model}...")
                
                # Call Ollama API
                system = f"You are helpful assistant with access to memory storage through the Engram system with client ID {args.client_id}."
                response = chat_with_ollama(args.model, chat_history, system, 0.7)
                
                if "message" in response:
                    assistant_message = response["message"]["content"]
                    print(f"\n{args.model}: {assistant_message}")
                    
                    # Add to chat history
                    chat_history.append({"role": "assistant", "content": assistant_message})
                    
                    # Store in memory if content is substantial
                    if len(user_input) > 10 and len(assistant_message) > 30:
                        try:
                            memory_service.store(
                                f"User: {user_input}\nAssistant: {assistant_message[:100]}...",
                                compartment_id="conversations", 
                                metadata={"source": args.model}
                            )
                            # Log successful memory storage
                            logger.info(f"Stored conversation in memory")
                        except Exception as mem_err:
                            logger.error(f"Failed to store in memory: {str(mem_err)}")
                else:
                    print("Error: No response from model")
            
            except KeyboardInterrupt:
                print("\nChat interrupted. Exiting.")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
                logger.error(f"Chat error: {str(e)}")
                # Brief pause before continuing to prevent error flooding
                time.sleep(1)
        
    except Exception as e:
        logger.error(f"Failed to run Ollama bridge: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()