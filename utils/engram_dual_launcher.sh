#!/bin/bash
# Engram Dual Mode Launcher
# Launches both the HTTP and MCP servers for Engram memory system from any directory

# ANSI color codes for terminal output
BLUE="\033[94m"
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd )"

# Determine Engram directory if running from utils
if [[ "$SCRIPT_DIR" == */utils ]]; then
    ENGRAM_DIR="$(dirname "$SCRIPT_DIR")"
else
    ENGRAM_DIR="$SCRIPT_DIR"
fi

# Default settings
CLIENT_ID="claude"
HTTP_PORT=8000
MCP_PORT=8001
HOST="127.0.0.1"
DATA_DIR="$HOME/.engram"
FALLBACK=false
DEBUG=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --client-id)
      CLIENT_ID="$2"
      shift 2
      ;;
    --http-port)
      HTTP_PORT="$2"
      shift 2
      ;;
    --mcp-port)
      MCP_PORT="$2"
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
    --fallback)
      FALLBACK=true
      shift
      ;;
    --debug)
      DEBUG=true
      shift
      ;;
    --help)
      echo -e "${BLUE}${BOLD}Engram Dual Mode Launcher${RESET}"
      echo "Usage: engram_dual_launcher.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --client-id <id>    Client ID for memory service (default: claude)"
      echo "  --http-port <port>  Port for HTTP server (default: 8000)"
      echo "  --mcp-port <port>   Port for MCP server (default: 8001)"
      echo "  --host <host>       Host to bind the servers to (default: 127.0.0.1)"
      echo "  --data-dir <dir>    Directory to store memory data (default: ~/.engram)"
      echo "  --fallback          Use fallback file-based implementation"
      echo "  --debug             Enable debug mode"
      echo "  --help              Show this help message"
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

# Check if Engram dual script exists
DUAL_SCRIPT="$ENGRAM_DIR/engram_dual"
if [ ! -f "$DUAL_SCRIPT" ]; then
    echo -e "${RED}Error: Could not find engram_dual script at $DUAL_SCRIPT${RESET}"
    echo -e "${RED}Please make sure Engram is properly installed${RESET}"
    exit 1
fi

# Make sure the script is executable
chmod +x "$DUAL_SCRIPT"

# Build the command
CMD=("$DUAL_SCRIPT")
CMD+=("--client-id" "$CLIENT_ID")
CMD+=("--http-port" "$HTTP_PORT")
CMD+=("--mcp-port" "$MCP_PORT")
CMD+=("--host" "$HOST")

if [ -n "$DATA_DIR" ]; then
    CMD+=("--data-dir" "$DATA_DIR")
fi

if [ "$FALLBACK" = true ]; then
    CMD+=("--fallback")
fi

if [ "$DEBUG" = true ]; then
    CMD+=("--debug")
fi

# Print banner
echo -e "${BOLD}${BLUE}===== Engram Dual Mode Launcher =====${RESET}"
echo -e "${BLUE}Starting Engram in dual mode (HTTP + MCP)${RESET}"

# Execute the command
echo -e "${GREEN}Launching with the following settings:${RESET}"
echo -e "  ${YELLOW}Client ID:${RESET} $CLIENT_ID"
echo -e "  ${YELLOW}HTTP Server:${RESET} $HOST:$HTTP_PORT"
echo -e "  ${YELLOW}MCP Server:${RESET} $HOST:$MCP_PORT"
echo -e "  ${YELLOW}Data Directory:${RESET} $DATA_DIR"
echo -e "  ${YELLOW}Fallback Mode:${RESET} $FALLBACK"
echo -e "  ${YELLOW}Debug Mode:${RESET} $DEBUG"
echo ""

# Execute the dual server
"${CMD[@]}"
