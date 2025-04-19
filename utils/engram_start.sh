#!/bin/bash
# Engram Start Script
# Starts the Engram consolidated memory service

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Default settings
CLIENT_ID="claude"
PORT=8000
HOST="127.0.0.1"
DATA_DIR="$HOME/.engram"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --client-id)
      CLIENT_ID="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --host)
      HOST="$2"
      shift 2
      ;;
    --data-dir)
      DATA_DIR="$2"
      shift 2
      ;;
    --help)
      echo -e "${BLUE}${BOLD}Engram Memory Service${NC}"
      echo "Usage: engram_start.sh [options]"
      echo ""
      echo "Options:"
      echo "  --client-id <id>   Client ID for memory service (default: claude)"
      echo "  --port <port>      Port to run the server on (default: 8000)"
      echo "  --host <host>      Host to bind the server to (default: 127.0.0.1)"
      echo "  --data-dir <dir>   Directory to store memory data (default: ~/.engram)"
      echo "  --help             Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage information"
      exit 1
      ;;
  esac
done

# Make sure the data directory exists
mkdir -p "$DATA_DIR"

# Check for virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo -e "${YELLOW}No virtual environment found in $SCRIPT_DIR/venv${NC}"
    echo -e "${YELLOW}Using system Python environment${NC}"
fi

# Check if the consolidated server script exists
if [ -f "$SCRIPT_DIR/engram_consolidated" ]; then
    echo -e "${GREEN}Starting Engram...${NC}"
    echo -e "${BLUE}Client ID:${NC} $CLIENT_ID"
    echo -e "${BLUE}Server:${NC} $HOST:$PORT"
    echo -e "${BLUE}Data directory:${NC} $DATA_DIR"
    echo ""
    
    # Run the consolidated server
    "$SCRIPT_DIR/engram_consolidated" --client-id "$CLIENT_ID" --port "$PORT" --host "$HOST" --data-dir "$DATA_DIR" "$@"
else
    echo -e "${RED}Error: Could not find engram_consolidated script${NC}"
    echo -e "${RED}Please make sure you're running this from the Engram directory${NC}"
    exit 1
fi