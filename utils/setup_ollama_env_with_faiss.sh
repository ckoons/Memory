#!/bin/bash
# Setup Ollama Environment for Engram with FAISS vector database
# This script creates a virtual environment with NumPy 2.x and FAISS

set -e  # Exit on any error

# Configuration
VENV_NAME="vector/ollama_faiss_venv"

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

# Install dependencies with NumPy 2.x compatibility
echo "Installing dependencies with NumPy 2.x compatibility..."
pip install numpy>=2.0.0
pip install -r requirements.txt

# Remove chromadb and qdrant-client if installed
pip uninstall -y chromadb qdrant-client sentence-transformers

# Install FAISS (works with NumPy 2.x)
echo "Installing FAISS vector database (NumPy 2.x compatible)..."
pip install faiss-cpu>=1.7.0
pip install tqdm>=4.27.0

# Create a modified vector database adapter file
echo "Creating FAISS adapter for Engram..."
cat > faiss_adapter.py <<EOL
#!/usr/bin/env python3
"""
FAISS Vector Database Adapter for Engram
This module provides a compatibility layer between Engram and FAISS.
"""

import os
import sys
import faiss
import numpy as np
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Directory for storing FAISS indices
FAISS_DIR = os.path.join(os.path.expanduser("~"), ".engram", "faiss_indices")
os.makedirs(FAISS_DIR, exist_ok=True)

class VectorIndexManager:
    """Manager for FAISS vector indices to enable semantic search."""
    
    def __init__(self, namespace: str = "default"):
        """Initialize the vector index manager."""
        self.namespace = namespace
        self.index_path = os.path.join(FAISS_DIR, f"{namespace}.index")
        self.metadata_path = os.path.join(FAISS_DIR, f"{namespace}.json")
        self.dimension = 1536  # Default dimension for text embeddings
        
        # Create or load the index
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create a new one."""
        try:
            if os.path.exists(self.index_path):
                # Load existing index
                self.index = faiss.read_index(self.index_path)
                # Load metadata
                if os.path.exists(self.metadata_path):
                    with open(self.metadata_path, "r") as f:
                        self.metadata = json.load(f)
                else:
                    self.metadata = {"documents": [], "ids": []}
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = {"documents": [], "ids": []}
        except Exception as e:
            print(f"Error loading/creating index: {e}")
            # Create fallback index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = {"documents": [], "ids": []}
    
    def _save_index(self):
        """Save the index and metadata to disk."""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w") as f:
                json.dump(self.metadata, f)
        except Exception as e:
            print(f"Error saving index: {e}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate an embedding for text using FAISS."""
        # Simple embedding function - in a real system, use a proper model
        # This is just a placeholder that creates deterministic vectors
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_val = int(hash_obj.hexdigest(), 16)
        np.random.seed(hash_val)
        embedding = np.random.normal(0, 1, self.dimension).astype(np.float32)
        # Normalize to unit length
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    def add(self, document: str, doc_id: Optional[str] = None) -> str:
        """Add a document to the vector index."""
        if doc_id is None:
            doc_id = f"{int(time.time())}_{len(self.metadata['documents'])}"
        
        # Generate embedding
        embedding = self.generate_embedding(document)
        
        # Add to index
        self.index.add(np.array([embedding]))
        
        # Add to metadata
        self.metadata["documents"].append(document)
        self.metadata["ids"].append(doc_id)
        
        # Save changes
        self._save_index()
        
        return doc_id
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity."""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search the index
        distances, indices = self.index.search(np.array([query_embedding]), limit)
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.metadata["documents"]):
                continue
                
            results.append({
                "id": self.metadata["ids"][idx],
                "content": self.metadata["documents"][idx],
                "relevance": float(1.0 / (1.0 + distances[0][i])),
            })
        
        return results

# Example of how to use with Engram
def install_faiss_adapter():
    """Install the FAISS adapter into Engram."""
    try:
        from engram.core import memory
        
        # Monkey patch the vector database functions
        memory.HAS_VECTOR_DB = True
        memory.VECTOR_DB_NAME = "FAISS"
        
        # Check if the semantic_search method exists before patching
        if hasattr(memory.MemoryService, 'semantic_search'):
            # Original semantic search function exists, so patch it
            original_semantic_search = memory.MemoryService.semantic_search
            
            def patched_semantic_search(self, query, namespace="default", limit=5):
                """Patched semantic search using FAISS."""
                try:
                    # Try using our FAISS adapter
                    manager = VectorIndexManager(namespace)
                    results = manager.search(query, limit)
                    return {
                        "count": len(results),
                        "results": results
                    }
                except Exception as e:
                    print(f"FAISS search error: {e}")
                    # Fall back to original implementation
                    return original_semantic_search(self, query, namespace, limit)
            
            # Apply the patch
            memory.MemoryService.semantic_search = patched_semantic_search
        else:
            # Method doesn't exist, so add it
            print("Adding new semantic_search method to MemoryService")
            
            async def new_semantic_search(self, query, namespace="default", limit=5):
                """New semantic search method using FAISS."""
                try:
                    # Use our FAISS adapter
                    manager = VectorIndexManager(namespace)
                    results = manager.search(query, limit)
                    return {
                        "count": len(results),
                        "results": results
                    }
                except Exception as e:
                    print(f"FAISS search error: {e}")
                    # Return empty results
                    return {"count": 0, "results": []}
            
            # Add the method
            setattr(memory.MemoryService, 'semantic_search', new_semantic_search)
        
        # Original add function with vector embedding
        original_add = memory.MemoryService.add
        
        async def patched_add(self, content, namespace="default", metadata=None):
            """Patched add method to store in FAISS as well."""
            # Call original implementation
            result = await original_add(self, content, namespace, metadata)
            
            # Also add to FAISS index
            try:
                manager = VectorIndexManager(namespace)
                doc_id = result.get("id", str(int(time.time())))
                manager.add(content, doc_id)
            except Exception as e:
                print(f"FAISS add error: {e}")
            
            return result
        
        # Apply the patch
        memory.MemoryService.add = patched_add
        
        return True
    except Exception as e:
        print(f"Failed to install FAISS adapter: {e}")
        return False

# If this file is run directly, install the adapter
if __name__ == "__main__":
    install_faiss_adapter()
EOL

# Create a launcher script for the virtual environment
echo "Creating launcher script..."
cat > ../engram_with_ollama_faiss <<EOL
#!/bin/bash
# Engram with Ollama - Fixed launcher script with FAISS vector database

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
      echo "Engram with Ollama - Launcher script with FAISS vector database"
      echo ""
      echo "Usage: engram_with_ollama_faiss [options]"
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
source "\$SCRIPT_DIR/../$VENV_NAME/bin/activate"

# Install FAISS adapter
echo "Installing FAISS adapter for Engram..."

# Create a simple adapter installer script
cat > "\$SCRIPT_DIR/install_faiss_adapter.py" << 'EOF'
#!/usr/bin/env python3
import os
import sys
import importlib.util

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Try to import the FAISS adapter
try:
    spec = importlib.util.spec_from_file_location("faiss_adapter", 
                                                 os.path.join(project_dir, "faiss_adapter.py"))
    faiss_adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(faiss_adapter)
    
    # Call the install function
    success = faiss_adapter.install_faiss_adapter()
    if success:
        print("FAISS adapter installed successfully!")
    else:
        print("FAISS adapter installation may have failed.")
except Exception as e:
    print(f"Error importing or running FAISS adapter: {e}")
    sys.exit(1)
EOF

# Make it executable
chmod +x "\$SCRIPT_DIR/install_faiss_adapter.py"

# Run the installer
python "\$SCRIPT_DIR/install_faiss_adapter.py"

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

# Start the Ollama bridge
echo "Starting Ollama bridge with Engram memory using FAISS..."
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
chmod +x ../engram_with_ollama_faiss

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "To use Ollama with Engram and FAISS vector database, run:"
echo "./engram_with_ollama_faiss"
echo ""
echo "This will launch Ollama with a NumPy 2.x compatible vector database."
echo "The script uses FAISS instead of ChromaDB, which works with NumPy 2.x."
echo ""
echo "For more options:"
echo "./engram_with_ollama_faiss --help"

# Deactivate virtual environment
deactivate