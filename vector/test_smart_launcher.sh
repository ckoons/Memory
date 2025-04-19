#!/bin/bash
# Test script for the Engram smart launcher system

# Get directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENGRAM_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$ENGRAM_DIR"

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}Engram Smart Launcher Test${NC}"
echo -e "${BLUE}Testing vector database detection and launcher selection...${NC}"
echo ""

# Test vector database detection
echo -e "${BLUE}Testing vector database detection:${NC}"
echo -e "${YELLOW}Running: python utils/detect_best_vector_db.py${NC}"
echo ""
python utils/detect_best_vector_db.py
echo ""

# Test smart launcher with Claude
echo -e "${BLUE}Testing smart launcher with Claude:${NC}"
echo -e "${YELLOW}Running: ./engram_smart_launch --test${NC}"
LAUNCHER=$(python utils/detect_best_vector_db.py --quiet)
echo -e "${GREEN}Would launch: ${LAUNCHER}${NC}"
echo ""

# Test smart launcher with Ollama
echo -e "${BLUE}Testing smart launcher with Ollama:${NC}"
echo -e "${YELLOW}Running: ./engram_smart_launch_ollama --test${NC}"
LAUNCHER=$(python utils/detect_best_vector_db.py --quiet --ollama)
echo -e "${GREEN}Would launch: ${LAUNCHER}${NC}"
echo ""

# Test vector database functionality
echo -e "${BLUE}Testing vector database implementations:${NC}"
echo -e "${YELLOW}Running: python vector/lancedb/test_vector_db.py${NC}"
echo ""
python vector/lancedb/test_vector_db.py
echo ""

echo -e "${CYAN}${BOLD}Test Complete${NC}"