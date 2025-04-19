"""
Engram Consolidated API Server

A unified FastAPI server that provides both core memory services and HTTP wrapper
functionality on a single port. This eliminates the need for multiple ports.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../.."))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.api.server")

# Check if we're in fallback mode (set by engram_consolidated script)
USE_FALLBACK = os.environ.get('ENGRAM_USE_FALLBACK', '').lower() in ('1', 'true', 'yes')

# Import dependencies and controllers
from engram.core.config import get_config
from engram.core.memory_manager import MemoryManager
from engram.api.dependencies import default_client_id, memory_manager

# Initialize dependencies manually since we've removed the lifespan function
default_client_id = os.environ.get("ENGRAM_CLIENT_ID", "claude")
data_dir = os.environ.get("ENGRAM_DATA_DIR", None)
try:
    memory_manager = MemoryManager(data_dir=data_dir)
    logger.info(f"Memory manager initialized directly with data directory: {data_dir or '~/.engram'}")
    logger.info(f"Default client ID: {default_client_id}")
except Exception as e:
    logger.error(f"Failed to initialize memory manager: {e}")
    memory_manager = None
from engram.api.controllers.root import router as root_router
from engram.api.controllers.core_memory import router as core_router
from engram.api.controllers.http_wrapper import router as http_router
from engram.api.controllers.compartments import router as compartment_router
from engram.api.controllers.private import router as private_router
from engram.api.controllers.structured import router as structured_router
from engram.api.controllers.nexus import router as nexus_router
from engram.api.controllers.clients import router as clients_router


# Lifecycle management removed for stability
# The code below used to be a lifespan function that managed initialization and cleanup
# It caused startup issues and has been removed in favor of direct initialization
# 
# A future implementation could add back proper lifecycle management with:
# - Proper error handling
# - Timeouts to prevent hanging
# - Resilient design allowing for partial initialization
#
# For now, initialization happens at module level (see above)


# Initialize FastAPI app - removed lifespan for stability testing
app = FastAPI(
    title="Engram Consolidated API",
    description="Unified API for Engram combining core memory services and HTTP wrapper",
    version="0.7.0"
    # lifespan parameter removed to test if this fixes startup issues
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(root_router)
app.include_router(core_router)
app.include_router(http_router)
app.include_router(compartment_router)
app.include_router(private_router)
app.include_router(structured_router)
app.include_router(nexus_router)
app.include_router(clients_router)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Engram Consolidated API Server")
    parser.add_argument("--client-id", type=str, default=None,
                      help="Client ID for memory service")
    parser.add_argument("--port", type=int, default=None,
                      help="Port to run the server on")
    parser.add_argument("--host", type=str, default=None,
                      help="Host to bind the server to")
    parser.add_argument("--data-dir", type=str, default=None,
                      help="Directory to store memory data")
    parser.add_argument("--config", type=str, default=None,
                      help="Path to custom config file")
    parser.add_argument("--fallback", action="store_true",
                      help="Use fallback file-based implementation without vector database")
    parser.add_argument("--no-auto-agency", action="store_true",
                      help="Disable automatic agency activation")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug mode")
    return parser.parse_args()


def main():
    """Main entry point for the CLI command."""
    args = parse_arguments()
    
    # Load configuration
    config = get_config(args.config)
    
    # Override with command line arguments if provided
    if args.client_id:
        config["client_id"] = args.client_id
    if args.data_dir:
        config["data_dir"] = args.data_dir
    if args.port:
        config["port"] = args.port
    if args.host:
        config["host"] = args.host
    if args.no_auto_agency:
        config["auto_agency"] = False
    if args.debug:
        config["debug"] = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Set environment variables for default client ID and data directory
    # Note: The client_id is now just a default - multiple clients are supported
    os.environ["ENGRAM_CLIENT_ID"] = config["client_id"]
    os.environ["ENGRAM_DATA_DIR"] = config["data_dir"]
    
    # Set fallback mode if requested
    if args.fallback:
        os.environ["ENGRAM_USE_FALLBACK"] = "1"
        logger.info("Fallback mode enabled: Using file-based implementation without vector database")
    
    # Start the server
    logger.info(f"Starting Engram consolidated server on {config['host']}:{config['port']}")
    logger.info(f"Default client ID: {config['client_id']}, Data directory: {config['data_dir']}")
    logger.info(f"Multiple client IDs are supported - use the X-Client-ID header to specify")
    logger.info(f"Auto-agency: {'enabled' if config['auto_agency'] else 'disabled'}")
    
    if config["debug"]:
        logger.info("Debug mode enabled")
    
    uvicorn.run(app, host=config["host"], port=config["port"])


if __name__ == "__main__":
    main()