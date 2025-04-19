#!/bin/bash
# Simple script to launch a Claude instance with a specific client ID

# Check if client ID was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <client_id>"
  echo "Example: $0 claude3"
  exit 1
fi

CLIENT_ID="$1"
echo "Launching Claude with client ID: $CLIENT_ID"

# Set environment variables
export ENGRAM_CLIENT_ID="$CLIENT_ID"
export ENGRAM_DATA_DIR="$HOME/.engram"

# Launch Claude
claude --allowedTools="Bash(*),Edit,View,Replace,BatchTool,GlobTool,GrepTool,LS,ReadNotebook,NotebookEditCell,WebFetchTool"