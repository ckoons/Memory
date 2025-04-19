#!/usr/bin/env python3
"""
Ollama MCP Test Client

This script tests the Ollama MCP server by making requests to its endpoints
and verifying the responses.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ollama_mcp_test")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ollama MCP Test Client")
    parser.add_argument("--host", type=str, default="http://localhost:8002",
                      help="Ollama MCP server host")
    parser.add_argument("--model", type=str, default="llama3",
                      help="Model to test with")
    parser.add_argument("--prompt", type=str, default="Explain how MCP protocol works in 2-3 sentences.",
                      help="Prompt to use for testing")
    parser.add_argument("--test-all", action="store_true",
                      help="Test all capabilities")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    return parser.parse_args()

async def test_health(host: str) -> bool:
    """Test the health endpoint."""
    try:
        url = f"{host}/health"
        logger.info(f"Testing health endpoint: {url}")
        
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Health check result: {result}")
            return True
        else:
            logger.error(f"Health check failed with status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        return False

async def test_manifest(host: str) -> Dict[str, Any]:
    """Test the manifest endpoint."""
    try:
        url = f"{host}/manifest"
        logger.info(f"Testing manifest endpoint: {url}")
        
        response = requests.get(url)
        if response.status_code == 200:
            manifest = response.json()
            logger.info(f"Server name: {manifest.get('name')}")
            logger.info(f"Server version: {manifest.get('version')}")
            logger.info(f"Available capabilities: {', '.join(manifest.get('capabilities', {}).keys())}")
            return manifest
        else:
            logger.error(f"Manifest request failed with status {response.status_code}: {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching manifest: {e}")
        return {}

async def test_ollama_tags(host: str) -> List[str]:
    """Test the ollama_tags capability."""
    try:
        url = f"{host}/invoke"
        logger.info(f"Testing ollama_tags capability")
        
        payload = {
            "capability": "ollama_tags",
            "parameters": {}
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            models = [model.get("name") for model in result.get("models", [])]
            logger.info(f"Available models: {', '.join(models[:5])}...")
            logger.info(f"Total models: {result.get('total', 0)}")
            return models
        else:
            logger.error(f"ollama_tags request failed with status {response.status_code}: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        return []

async def test_ollama_generate(host: str, model: str, prompt: str) -> str:
    """Test the ollama_generate capability."""
    try:
        url = f"{host}/invoke"
        logger.info(f"Testing ollama_generate capability with model {model}")
        
        payload = {
            "capability": "ollama_generate",
            "parameters": {
                "model": model,
                "prompt": prompt,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 100
                }
            }
        }
        
        logger.info(f"Prompt: {prompt}")
        start_time = time.time()
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result.get("content", "")
            duration = time.time() - start_time
            
            logger.info(f"Response (in {duration:.2f}s): {content}")
            logger.info(f"Total duration: {result.get('total_duration', 0):.2f}ms")
            return content
        else:
            logger.error(f"ollama_generate request failed with status {response.status_code}: {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return ""

async def test_ollama_chat(host: str, model: str, message: str) -> str:
    """Test the ollama_chat capability."""
    try:
        url = f"{host}/invoke"
        logger.info(f"Testing ollama_chat capability with model {model}")
        
        payload = {
            "capability": "ollama_chat",
            "parameters": {
                "model": model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        }
        
        logger.info(f"Message: {message}")
        start_time = time.time()
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            duration = time.time() - start_time
            
            logger.info(f"Response (in {duration:.2f}s): {content}")
            logger.info(f"Total duration: {result.get('total_duration', 0):.2f}ms")
            return content
        else:
            logger.error(f"ollama_chat request failed with status {response.status_code}: {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return ""

async def test_ollama_memory_chat(host: str, model: str, message: str) -> str:
    """Test the ollama_memory_chat capability."""
    try:
        url = f"{host}/invoke"
        logger.info(f"Testing ollama_memory_chat capability with model {model}")
        
        payload = {
            "capability": "ollama_memory_chat",
            "parameters": {
                "model": model,
                "messages": [
                    {"role": "user", "content": message}
                ],
                "client_id": "test_client",
                "memory_prompt_type": "combined",
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        }
        
        logger.info(f"Message: {message}")
        start_time = time.time()
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            content = result.get("message", {}).get("content", "")
            duration = time.time() - start_time
            
            logger.info(f"Response (in {duration:.2f}s): {content}")
            logger.info(f"Memory enhanced: {result.get('memory_enhanced', False)}")
            if "memory_operations" in result:
                logger.info(f"Memory operations: {len(result.get('memory_operations', []))}")
            
            return content
        else:
            logger.error(f"ollama_memory_chat request failed with status {response.status_code}: {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Error in memory chat: {e}")
        return ""

async def run_tests(args):
    """Run all tests."""
    logger.info(f"Testing Ollama MCP server at {args.host}")
    
    # Test health endpoint
    health_ok = await test_health(args.host)
    if not health_ok:
        logger.error("Health check failed, aborting tests")
        return
    
    # Test manifest endpoint
    manifest = await test_manifest(args.host)
    if not manifest:
        logger.error("Manifest request failed, aborting tests")
        return
    
    # Test ollama_tags capability
    models = await test_ollama_tags(args.host)
    if not models:
        logger.warning("No models found or tags request failed")
    
    # Check if the specified model is available
    model_to_use = args.model
    if models and args.model not in models:
        logger.warning(f"Specified model {args.model} not found in available models")
        model_to_use = models[0] if models else args.model
        logger.info(f"Using fallback model: {model_to_use}")
    
    # Test ollama_generate capability
    await test_ollama_generate(args.host, model_to_use, args.prompt)
    
    # Test ollama_chat capability
    await test_ollama_chat(args.host, model_to_use, args.prompt)
    
    # Test ollama_memory_chat capability
    await test_ollama_memory_chat(args.host, model_to_use, args.prompt + " Remember this information for future reference.")
    
    logger.info("All tests completed!")

def main():
    """Main function."""
    args = parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    asyncio.run(run_tests(args))

if __name__ == "__main__":
    main()