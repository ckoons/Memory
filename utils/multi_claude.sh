#!/bin/bash
# Launch multiple Claude instances for multi-agent collaboration

# Navigate to the project directory
cd "$(dirname "$0")"
# Launch multiple Claude instances
python -m engram.cli.claude_launcher multi --spec claude_instances.json