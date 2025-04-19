#!/usr/bin/env python3
"""
Test script for Ollama integration with Engram.

This script tests the Ollama system prompts and communication capabilities.
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test Ollama integration with Engram")
    parser.add_argument("--model", type=str, default="llama3:8b", help="Ollama model to test")
    parser.add_argument("--prompt-type", type=str, choices=["memory", "communication", "combined"], 
                        default="combined", help="Type of system prompt to test")
    parser.add_argument("--test-type", type=str, choices=["system", "memory", "communication", "all"], 
                        default="all", help="Type of test to run")
    return parser.parse_args()

def test_system_prompts(model, prompt_type):
    """Test system prompt generation."""
    print(f"\n=== Testing System Prompts for {model} ({prompt_type}) ===\n")
    
    try:
        # Import the system prompt generator
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from ollama_system_prompts import (
            get_memory_system_prompt,
            get_communication_system_prompt,
            get_combined_system_prompt,
            get_model_capabilities
        )
        
        # Get model capabilities
        capabilities = get_model_capabilities(model)
        print(f"Model capabilities:")
        print(f"- Memory commands: {', '.join(capabilities['memory_cmds'])}")
        print(f"- Communication commands: {', '.join(capabilities['comm_cmds'])}")
        print(f"- Vector support: {capabilities['supports_vector']}")
        print(f"- Persona: {capabilities['persona']}")
        
        # Get the appropriate system prompt based on type
        if prompt_type == "memory":
            prompt = get_memory_system_prompt(model)
        elif prompt_type == "communication":
            prompt = get_communication_system_prompt(model)
        else:  # combined
            prompt = get_combined_system_prompt(model)
        
        # Print the prompt with line numbers
        print("\nGenerated System Prompt:")
        for i, line in enumerate(prompt.split('\n')):
            print(f"{i+1:3d}| {line}")
            
        return True
    except Exception as e:
        print(f"Error testing system prompts: {e}")
        return False

def test_memory_operations(model, prompt_type):
    """Test memory operations with Ollama."""
    print(f"\n=== Testing Memory Operations for {model} ===\n")
    
    try:
        # Start the Engram memory service if not already running
        try:
            subprocess.run(["./engram_start.sh"], check=True, capture_output=True, text=True)
            print("Started Engram memory service")
        except subprocess.CalledProcessError:
            print("Engram memory service already running or encountered an error")
        
        # Generate a test file with memory commands
        test_file = f"test_ollama_memory_{int(time.time())}.txt"
        with open(test_file, "w") as f:
            f.write("Hello! I'm going to test my memory capabilities.\n\n")
            f.write("REMEMBER: This is a test memory from the Ollama integration test.\n\n")
            f.write("Now I'll search for memories about tests:\n")
            f.write("SEARCH: test\n\n")
            f.write("Let me list some recent memories:\n")
            f.write("RETRIEVE: 3\n\n")
            f.write("Let me try context retrieval:\n")
            f.write("CONTEXT: integration testing\n\n")
            f.write("I'll also try semantic search:\n")
            f.write("SEMANTIC: system test\n\n")
            f.write("I'll remember something else that should be forgotten:\n")
            f.write("REMEMBER: Temporary test data to be deleted.\n\n")
            f.write("Now I'll mark it to be forgotten:\n")
            f.write("FORGET: Temporary test data\n\n")
            f.write("That's the end of the memory test!")
        
        # Run the Ollama bridge with the test file as input
        print("Running Ollama bridge with memory test")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = [
            "python", os.path.join(script_dir, "ollama_bridge.py"), 
            model, 
            "--prompt-type", prompt_type,
            "--memory-functions"
        ]
        
        # Pass the test file as input
        with open(test_file, "r") as f:
            test_input = f.read()
            
        try:
            # Start the process
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for initialization
            time.sleep(2)
            
            # Send "n" to skip including recent memories
            proc.stdin.write("n\n")
            proc.stdin.flush()
            
            # Wait a bit before sending test input
            time.sleep(1)
            
            # Send each line of test input
            for line in test_input.split('\n'):
                proc.stdin.write(f"{line}\n")
                proc.stdin.flush()
                time.sleep(0.5)  # Give time for processing
            
            # Send exit command
            proc.stdin.write("exit\n")
            proc.stdin.flush()
            
            # Wait for response with timeout
            try:
                stdout, stderr = proc.communicate(timeout=60)
                print("\nOutput from Ollama bridge:")
                print(stdout)
                if stderr:
                    print("\nErrors:")
                    print(stderr)
            except subprocess.TimeoutExpired:
                proc.kill()
                print("Process timed out, killed")
                stdout, stderr = proc.communicate()
        
        except Exception as e:
            print(f"Error running Ollama bridge: {e}")
            return False
        
        # Clean up
        try:
            os.remove(test_file)
        except:
            pass
        
        return True
    except Exception as e:
        print(f"Error testing memory operations: {e}")
        return False

def test_communication(model, prompt_type):
    """Test communication between Ollama and Claude."""
    print(f"\n=== Testing Communication for {model} ===\n")
    
    try:
        # Generate a test file with communication commands
        test_file = f"test_ollama_comm_{int(time.time())}.txt"
        with open(test_file, "w") as f:
            f.write("Hello! I'm going to test my communication capabilities.\n\n")
            f.write("SEND TO Claude: Hello Claude! This is a test message from the Ollama integration test.\n\n")
            f.write("Now I'll check for messages from Claude:\n")
            f.write("CHECK MESSAGES FROM Claude\n\n")
            f.write("I'll send a reply to Claude:\n")
            f.write("REPLY TO Claude: Thanks for any response you've sent. This is a follow-up message in our test conversation.\n\n")
            f.write("Finally, I'll try broadcasting a message to all AIs:\n")
            f.write("BROADCAST: This is a broadcast test message to all available AI models.\n\n")
            f.write("That's the end of the communication test!")
        
        # Run the Ollama bridge with the test file as input
        print("Running Ollama bridge with communication test")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = [
            "python", os.path.join(script_dir, "ollama_bridge.py"), 
            model, 
            "--prompt-type", prompt_type,
            "--memory-functions",
            "--available-models", "Claude", "Echo", "Mix"
        ]
        
        # Pass the test file as input
        with open(test_file, "r") as f:
            test_input = f.read()
            
        try:
            # Start the process
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for initialization
            time.sleep(2)
            
            # Send "n" to skip including recent memories
            proc.stdin.write("n\n")
            proc.stdin.flush()
            
            # Wait a bit before sending test input
            time.sleep(1)
            
            # Send each line of test input
            for line in test_input.split('\n'):
                proc.stdin.write(f"{line}\n")
                proc.stdin.flush()
                time.sleep(0.5)  # Give time for processing
            
            # Send exit command
            proc.stdin.write("exit\n")
            proc.stdin.flush()
            
            # Wait for response with timeout
            try:
                stdout, stderr = proc.communicate(timeout=60)
                print("\nOutput from Ollama bridge:")
                print(stdout)
                if stderr:
                    print("\nErrors:")
                    print(stderr)
            except subprocess.TimeoutExpired:
                proc.kill()
                print("Process timed out, killed")
                stdout, stderr = proc.communicate()
        
        except Exception as e:
            print(f"Error running Ollama bridge: {e}")
            return False
        
        # Clean up
        try:
            os.remove(test_file)
        except:
            pass
        
        return True
    except Exception as e:
        print(f"Error testing communication: {e}")
        return False

def main():
    """Main function."""
    args = parse_args()
    
    # Track test results
    results = {}
    
    # Run tests based on the test type
    if args.test_type in ["system", "all"]:
        results["system"] = test_system_prompts(args.model, args.prompt_type)
    
    if args.test_type in ["memory", "all"]:
        results["memory"] = test_memory_operations(args.model, args.prompt_type)
    
    if args.test_type in ["communication", "all"]:
        results["communication"] = test_communication(args.model, args.prompt_type)
    
    # Display summary
    print("\n=== Test Summary ===")
    for test, result in results.items():
        print(f"{test}: {'PASS' if result else 'FAIL'}")

if __name__ == "__main__":
    main()