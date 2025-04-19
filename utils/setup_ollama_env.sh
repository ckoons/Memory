#!/bin/bash
# Setup Ollama Environment for Engram
# This script creates a virtual environment with the correct dependencies for Ollama integration

set -e  # Exit on any error

# Configuration
VENV_NAME="ollama_venv"
REQUIRED_PYTHON_VERSION="3.10"  # Minimum version that works well with all dependencies

# Detect Python version
if command -v python3.10 &>/dev/null; then
    PYTHON="python3.10"
elif command -v python3.9 &>/dev/null; then
    PYTHON="python3.9"
elif command -v python3.8 &>/dev/null; then
    PYTHON="python3.8"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    echo "Error: Could not find Python 3. Please install Python 3.8 or newer."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "ollama/ollama_bridge.py" ]; then
    echo "Error: This script must be run from the Engram project directory."
    echo "Please navigate to the directory containing ollama/ollama_bridge.py."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment '$VENV_NAME' using $PYTHON..."
$PYTHON -m venv $VENV_NAME

# Activate virtual environment
source $VENV_NAME/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies with compatible versions
echo "Installing dependencies with compatible versions..."
pip install numpy==1.24.3  # Version 1.x is necessary for compatibility with sentence-transformers
pip install -r requirements.txt

# Install additional dependencies for Ollama integration with exact versions for compatibility
echo "Installing Ollama integration dependencies..."
pip install sentence-transformers==2.2.2
pip install chromadb==0.4.22

# Make sure qdrant-client is not installed (removing dependency if present)
pip uninstall -y qdrant-client

# Create a launcher script for the virtual environment
echo "Creating launcher script..."
cat > engram_with_ollama_fixed <<EOL
#!/bin/bash
# Engram with Ollama - Fixed launcher script with proper virtual environment

# Get directory of this script
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"

# Default values
MODEL="llama3:8b"
PROMPT_TYPE="combined"
CLIENT_ID="ollama"
TEMPERATURE="0.7"
MAX_TOKENS="2048"
MEMORY_FUNCTIONS=true
AVAILABLE_MODELS="Claude"

# Parse command-line arguments
while [[ \$# -gt 0 ]]; do
  case \$1 in
    --model)
      MODEL="\$2"
      shift 2
      ;;
    --prompt-type)
      PROMPT_TYPE="\$2"
      shift 2
      ;;
    --client-id)
      CLIENT_ID="\$2"
      shift 2
      ;;
    --temperature)
      TEMPERATURE="\$2"
      shift 2
      ;;
    --max-tokens)
      MAX_TOKENS="\$2"
      shift 2
      ;;
    --no-memory)
      MEMORY_FUNCTIONS=false
      shift
      ;;
    --available-models)
      AVAILABLE_MODELS="\$2"
      shift 2
      ;;
    --help)
      echo "Engram with Ollama - Launcher script with fixed environment"
      echo ""
      echo "Usage: engram_with_ollama_fixed [options]"
      echo ""
      echo "Options:"
      echo "  --model MODEL             Ollama model to use (default: llama3:8b)"
      echo "  --prompt-type TYPE        System prompt type: memory, communication, combined (default: combined)"
      echo "  --client-id ID            Client ID for Engram (default: ollama)"
      echo "  --temperature TEMP        Temperature for generation (default: 0.7)"
      echo "  --max-tokens TOKENS       Maximum tokens to generate (default: 2048)"
      echo "  --no-memory               Disable memory functions"
      echo "  --available-models MODELS Space-separated list of available models (default: Claude)"
      echo "  --help                    Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: \$1"
      echo "Use --help to see available options"
      exit 1
      ;;
  esac
done

# Store the current working directory
CURRENT_DIR="\$(pwd)"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
  echo "Error: Ollama is not running. Please start Ollama first."
  exit 1
fi

# Activate the virtual environment
source "\$SCRIPT_DIR/$VENV_NAME/bin/activate"

# Use absolute paths for Ollama bridge script
OLLAMA_BRIDGE="\$SCRIPT_DIR/ollama/ollama_bridge.py"

# Verify the bridge file exists
if [ ! -f "\$OLLAMA_BRIDGE" ]; then
  echo "Error: Ollama bridge script not found at \$OLLAMA_BRIDGE"
  echo "Please check the installation path or reinstall Engram"
  exit 1
fi

# Build command with full absolute paths for scripts but preserving current directory
CMD="python \$OLLAMA_BRIDGE \$MODEL --prompt-type \$PROMPT_TYPE --client-id \$CLIENT_ID --temperature \$TEMPERATURE --max-tokens \$MAX_TOKENS"

if [ "\$MEMORY_FUNCTIONS" = true ]; then
  CMD="\$CMD --memory-functions"
fi

for model in \$AVAILABLE_MODELS; do
  CMD="\$CMD --available-models \$model"
done

# Enable file-based memory only if vector database isn't working
# The virtual environment should have compatible NumPy, so we'll try without the fallback first
# export ENGRAM_USE_FALLBACK=1

# Start the Ollama bridge
echo "Starting Ollama bridge with Engram memory..."
echo "Model: \$MODEL"
echo "Prompt type: \$PROMPT_TYPE"
echo "Client ID: \$CLIENT_ID"
echo "Working directory: \$CURRENT_DIR"
echo ""
echo "Type 'exit' or '/quit' to exit"
echo ""

# Execute the command from the current directory
exec \$CMD
EOL

# Make the launcher script executable
chmod +x engram_with_ollama_fixed

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "To use Ollama with Engram, run:"
echo "./engram_with_ollama_fixed"
echo ""
echo "This will launch Ollama with a compatible environment."
echo "The script handles NumPy version compatibility automatically."
echo ""
echo "For more options:"
echo "./engram_with_ollama_fixed --help"

# Deactivate virtual environment
deactivate