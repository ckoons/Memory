#!/usr/bin/env python3
"""
Test script for privacy features in Claude Memory Bridge.

This script tests the privacy and encryption features of ClaudeMemoryBridge,
including private memory storage, retrieval, and key management.
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from engram.core.crypto import CryptoManager
from engram.cli.quickmem import private, review_private, p, v

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def log_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def log_error(message):
    print(f"{RED}✗ {message}{RESET}")

def log_info(message):
    print(f"{BLUE}ℹ {message}{RESET}")

def log_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")

def test_crypto_manager():
    """Test the CryptoManager class directly."""
    print(f"\n{BOLD}Testing CryptoManager...{RESET}")
    
    # Create a temporary test directory
    test_dir = os.path.join(script_dir, "test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    try:
        # Initialize crypto manager
        crypto = CryptoManager(data_dir=test_dir, client_id="test")
        log_info("Created CryptoManager instance")
        
        # Test key generation
        if crypto.primary_key and crypto.emergency_key:
            log_success("Primary and emergency keys generated")
        else:
            log_error("Failed to generate keys")
            return False
        
        # Test encryption
        test_data = "This is a test of the encryption system"
        try:
            key_id, encrypted_data = crypto.encrypt(test_data)
            log_success(f"Encrypted data with key ID: {key_id}")
        except Exception as e:
            log_error(f"Encryption failed: {e}")
            return False
        
        # Test decryption with primary key
        try:
            decrypted_data = crypto.decrypt(key_id, encrypted_data)
            if decrypted_data == test_data:
                log_success("Decryption with primary key successful")
            else:
                log_error(f"Decryption returned incorrect data: {decrypted_data}")
                return False
        except Exception as e:
            log_error(f"Decryption with primary key failed: {e}")
            return False
        
        # Test decryption with emergency key
        try:
            decrypted_data = crypto.decrypt(key_id, encrypted_data, use_emergency=True)
            if decrypted_data == test_data:
                log_success("Decryption with emergency key successful")
            else:
                log_error(f"Emergency decryption returned incorrect data: {decrypted_data}")
                return False
        except Exception as e:
            log_error(f"Decryption with emergency key failed: {e}")
            return False
        
        # Test key rotation
        try:
            old_primary_key = crypto.primary_key
            success = crypto.rotate_primary_key()
            if success and crypto.primary_key != old_primary_key:
                log_success("Primary key rotation successful")
            else:
                log_error("Primary key rotation failed")
                return False
            
            # Test decryption with new key
            decrypted_data = crypto.decrypt(key_id, encrypted_data)
            if decrypted_data == test_data:
                log_success("Decryption after key rotation successful")
            else:
                log_error("Decryption after key rotation failed")
                return False
        except Exception as e:
            log_error(f"Key rotation test failed: {e}")
            return False
        
        # Test key listing
        try:
            keys = crypto.list_keys()
            if keys and len(keys) > 0:
                log_success(f"Listed {len(keys)} keys")
            else:
                log_error("Key listing returned empty result")
                return False
        except Exception as e:
            log_error(f"Key listing failed: {e}")
            return False
        
        # Test key deletion
        try:
            success = crypto.delete_key(key_id)
            if success:
                log_success(f"Deleted key {key_id}")
            else:
                log_error(f"Failed to delete key {key_id}")
                return False
        except Exception as e:
            log_error(f"Key deletion failed: {e}")
            return False
        
        return True
    
    finally:
        # Clean up test directory
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

def test_quickmem_privacy():
    """Test the QuickMem privacy functions."""
    print(f"\n{BOLD}Testing QuickMem privacy functions...{RESET}")
    
    # Test private memory storage
    log_info("Testing private memory storage...")
    test_content = f"This is a private test memory created at {time.time()}"
    
    try:
        result = private(test_content)
        if result:
            log_success("Stored private memory")
            memory_id = result if isinstance(result, str) else None
        else:
            log_error("Failed to store private memory")
            return False
    except Exception as e:
        log_error(f"Private memory storage failed: {e}")
        return False
    
    # Test private memory listing
    log_info("Testing private memory listing...")
    try:
        memories = review_private()
        if memories and len(memories) > 0:
            log_success(f"Listed {len(memories)} private memories")
        else:
            log_warning("No private memories found or listing failed")
    except Exception as e:
        log_error(f"Private memory listing failed: {e}")
    
    # Test specific memory retrieval if we have an ID
    if memory_id:
        log_info(f"Testing retrieval of specific memory {memory_id}...")
        try:
            memory = review_private(memory_id)
            if memory:
                content = memory.get("content")
                if content == test_content:
                    log_success("Retrieved correct private memory content")
                else:
                    log_error(f"Retrieved incorrect content: {content}")
                    return False
            else:
                log_error("Failed to retrieve private memory")
                return False
        except Exception as e:
            log_error(f"Private memory retrieval failed: {e}")
            return False
    
    return True

def main():
    """Run all privacy tests."""
    print(f"{BOLD}{BLUE}==== Engram Memory Privacy Tests ===={RESET}\n")
    
    # Test CryptoManager
    crypto_success = test_crypto_manager()
    
    # Test QuickMem privacy functions
    quickmem_success = test_quickmem_privacy()
    
    # Summary
    print(f"\n{BOLD}Test Summary:{RESET}")
    if crypto_success:
        print(f"{GREEN}✓ CryptoManager tests passed{RESET}")
    else:
        print(f"{RED}✗ CryptoManager tests failed{RESET}")
    
    if quickmem_success:
        print(f"{GREEN}✓ QuickMem privacy tests passed{RESET}")
    else:
        print(f"{RED}✗ QuickMem privacy tests failed{RESET}")
    
    if crypto_success and quickmem_success:
        print(f"\n{GREEN}{BOLD}All privacy tests passed!{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}Some privacy tests failed.{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())