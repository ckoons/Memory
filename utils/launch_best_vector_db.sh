#!/bin/bash
# Automatic Vector Database Selection for Engram
# This script automatically selects the best vector database backend
# based on hardware and installed libraries

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENGRAM_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$ENGRAM_DIR"

# ANSI color codes
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Python 3 not found, trying python...${NC}"
    PYTHON_CMD="python"
    if ! command -v python &> /dev/null; then
        echo -e "${YELLOW}Python not found, defaulting to standard launcher${NC}"
        exec "$ENGRAM_DIR/engram_with_claude" "$@"
    fi
else
    PYTHON_CMD="python3"
fi

# Check for Ollama mode
OLLAMA_MODE=0
for arg in "$@"; do
    if [ "$arg" == "--ollama" ] || [ "$arg" == "-o" ]; then
        OLLAMA_MODE=1
        # Remove the ollama flag from arguments
        args=("$@")
        new_args=()
        for a in "${args[@]}"; do
            if [ "$a" != "--ollama" ] && [ "$a" != "-o" ]; then
                new_args+=("$a")
            fi
        done
        set -- "${new_args[@]}"
        break
    fi
done

# Show header
echo -e "${CYAN}${BOLD}Engram Vector Database Launcher${NC}"
echo -e "${BLUE}Detecting optimal vector database for your system...${NC}"

# Run the detection script
if [ $OLLAMA_MODE -eq 1 ]; then
    LAUNCHER=$($PYTHON_CMD "$ENGRAM_DIR/utils/detect_best_vector_db.py" --quiet --ollama)
    echo -e "${BLUE}Using Ollama integration mode${NC}"
else
    LAUNCHER=$($PYTHON_CMD "$ENGRAM_DIR/utils/detect_best_vector_db.py" --quiet)
fi

# Show status (non-quiet mode)
$PYTHON_CMD "$ENGRAM_DIR/utils/detect_best_vector_db.py"

# Check if launcher exists
if [ ! -f "$LAUNCHER" ]; then
    echo -e "${YELLOW}Recommended launcher not found: $LAUNCHER${NC}"
    echo -e "${YELLOW}Falling back to standard launcher${NC}"
    
    if [ $OLLAMA_MODE -eq 1 ]; then
        LAUNCHER="$ENGRAM_DIR/ollama/engram_with_ollama"
    else
        LAUNCHER="$ENGRAM_DIR/core/engram_with_claude"
    fi
fi

# Make executable if needed
chmod +x "$LAUNCHER"

# Launch with the best vector database
echo -e "${GREEN}${BOLD}Launching Engram with optimal vector database...${NC}"
echo -e "${BLUE}Using: $(basename "$LAUNCHER")${NC}"
echo ""

# Execute the launcher with all original arguments
exec "$LAUNCHER" "$@"