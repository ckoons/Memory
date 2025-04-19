#!/usr/bin/env python3
"""
Debug script to directly run the Engram server for testing
"""

import sys
import os
import logging
import asyncio
import uvicorn

# Configure verbose logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum verbosity
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.debug")

# Set environment variables
os.environ["ENGRAM_CLIENT_ID"] = "claude"
os.environ["ENGRAM_DATA_DIR"] = os.path.expanduser("~/.engram")
os.environ["ENGRAM_USE_FALLBACK"] = "1"  # Force fallback mode

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

async def run_server():
    try:
        # Import the FastAPI app
        logger.info("Importing FastAPI app from consolidated_server...")
        from engram.api.consolidated_server import app
        
        # Start the server
        logger.info("Starting uvicorn server...")
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=8000,
            log_level="debug"
        )
        server = uvicorn.Server(config)
        logger.info("Server configured, running...")
        await server.serve()
    except Exception as e:
        logger.error(f"Error starting server: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Debug server script starting...")
    asyncio.run(run_server())