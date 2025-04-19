#!/usr/bin/env python3
"""
Test Multi-Claude Communication

This script provides a simple way to test the multi-Claude communication system.
It loads the communication functions into the current Python environment and
provides a simple interface for sending and receiving messages.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

class MultiClaudeTest:
    """Simple interface for testing multi-Claude communication."""
    
    def __init__(self, client_id=None):
        """Initialize the test interface."""
        # Get client ID from environment or parameter
        self.client_id = client_id or os.environ.get("ENGRAM_CLIENT_ID", "unknown")
        print(f"Client ID: {self.client_id}")
        
        # Import communication functions
        try:
            from engram.cli.comm_quickmem import sm, gm, ho, cc, lc, sc, gc, cs, wi
            self.sm = sm  # Send message
            self.gm = gm  # Get messages
            self.ho = ho  # Handoff message
            self.cc = cc  # Create context
            self.lc = lc  # List contexts
            self.sc = sc  # Send to context
            self.gc = gc  # Get context messages
            self.cs = cs  # Check communication status
            self.wi = wi  # Who am I (get client ID)
            
            print("✅ Communication functions loaded!")
            print(f"🆔 You are Claude instance: {self.client_id}")
        except ImportError as e:
            print(f"❌ Error loading communication functions: {e}")
            sys.exit(1)
    
    def menu(self):
        """Display menu of available commands."""
        print("\n=== Multi-Claude Communication Test ===")
        print(f"Claude Instance: {self.client_id}")
        print("\nAvailable commands:")
        print("  1. Send message to another Claude")
        print("  2. Get messages")
        print("  3. Create context space")
        print("  4. Send message to context space")
        print("  5. Get messages from context space")
        print("  6. List available context spaces")
        print("  7. Check communication status")
        print("  8. Check who I am")
        print("  9. Exit")
        
        choice = input("\nEnter choice (1-9): ")
        self.handle_choice(choice)
    
    def handle_choice(self, choice):
        """Handle the user's menu choice."""
        if choice == '1':
            recipient = input("Enter recipient Claude ID: ")
            message = input("Enter message: ")
            result = self.sm(message, recipient=recipient)
            print(f"Message sent: {result}")
        
        elif choice == '2':
            results = self.gm()
            if not results:
                print("No messages found.")
            else:
                print(f"Found {len(results)} messages:")
                for msg in results:
                    print(f"From: {msg.get('sender')}, Type: {msg.get('type')}")
                    print(f"Content: {msg.get('content')}")
                    print("---")
        
        elif choice == '3':
            name = input("Enter context name: ")
            description = input("Enter description: ")
            result = self.cc(name, description)
            print(f"Context created: {result}")
        
        elif choice == '4':
            context_id = input("Enter context ID: ")
            message = input("Enter message: ")
            result = self.sc(context_id, message)
            print(f"Message sent to context: {result}")
        
        elif choice == '5':
            context_id = input("Enter context ID: ")
            results = self.gc(context_id)
            if not results:
                print("No messages found in context.")
            else:
                print(f"Found {len(results)} messages in context:")
                for msg in results:
                    print(f"From: {msg.get('sender')}, Type: {msg.get('type')}")
                    print(f"Content: {msg.get('content')}")
                    print("---")
        
        elif choice == '6':
            results = self.lc()
            if not results:
                print("No context spaces available.")
            else:
                print(f"Found {len(results)} context spaces:")
                for context in results:
                    print(f"ID: {context.get('id')}")
                    print(f"Name: {context.get('name')}")
                    print(f"Description: {context.get('description')}")
                    print(f"Created by: {context.get('created_by')}")
                    print("---")
        
        elif choice == '7':
            result = self.cs()
            print("Communication status:")
            print(f"Client ID: {result.get('client_id')}")
            print(f"Messages: {result.get('messages', [])}")
            print(f"Contexts: {result.get('contexts', [])}")
        
        elif choice == '8':
            result = self.wi()
            print(f"You are: {result}")
        
        elif choice == '9':
            print("Exiting...")
            sys.exit(0)
        
        else:
            print("Invalid choice. Please try again.")
        
        # Return to menu
        input("\nPress Enter to continue...")
        self.menu()

def main():
    """Main entry point."""
    # Get client ID from environment
    client_id = os.environ.get("ENGRAM_CLIENT_ID")
    
    # If not set, prompt for client ID
    if not client_id:
        client_id = input("Enter your Claude client ID: ")
        os.environ["ENGRAM_CLIENT_ID"] = client_id
    
    # Create test interface
    test = MultiClaudeTest(client_id)
    
    # Display menu
    test.menu()

if __name__ == "__main__":
    main()