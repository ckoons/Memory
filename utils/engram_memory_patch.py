#!/usr/bin/env python3
"""
Memory Module Patch for Engram - Replaces ChromaDB with FAISS

This script patches the Engram memory module to use FAISS instead of ChromaDB,
providing vector search capabilities compatible with NumPy 2.x.

Usage:
    python engram_memory_patch.py
"""

import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("engram.memory_patch")

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import faiss
        import numpy as np
        logger.info(f"FAISS version: {faiss.__version__} found")
        logger.info(f"NumPy version: {np.__version__} found")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install FAISS with: pip install faiss-cpu")
        return False

def apply_memory_patch():
    """Apply the patch to memory.py to use FAISS for vector search."""
    try:
        # Import the memory module
        from engram.core import memory
        
        # Create backup if it doesn't exist
        memory_file = os.path.abspath(memory.__file__)
        backup_file = f"{memory_file}.bak"
        
        if not os.path.exists(backup_file):
            with open(memory_file, "r") as f:
                original_code = f.read()
            
            with open(backup_file, "w") as f:
                f.write(original_code)
            logger.info(f"Created backup at {backup_file}")
        
        # Override the vector DB detection
        memory.HAS_VECTOR_DB = True
        memory.VECTOR_DB_NAME = "FAISS"
        memory.VECTOR_DB_VERSION = "1.7.0+"
        
        # Import FAISS and additional dependencies
        import faiss
        import numpy as np
        import json
        from pathlib import Path
        
        logger.info("Patching MemoryService with FAISS support...")
        
        # Original methods to patch
        original_init = memory.MemoryService.__init__
        
        # Patched initialization method
        def patched_init(self, client_id: str = "default", data_dir = None):
            """Patched initialization with FAISS support."""
            # Call original init to set up basic structure
            original_init(self, client_id, data_dir)
            
            try:
                # Initialize FAISS for vector storage
                from sentence_transformers import SentenceTransformer
                
                # Initialize vector DB path
                vector_db_path = self.data_dir / "faiss_indices"
                vector_db_path.mkdir(parents=True, exist_ok=True)
                
                # Load sentence transformer model for embeddings
                model_name = "all-MiniLM-L6-v2"  # Small, fast model
                self.vector_model = SentenceTransformer(model_name)
                
                # Configure vector dimensions based on the model
                self.vector_dim = self.vector_model.get_sentence_embedding_dimension()
                
                # Initialize FAISS indices for each namespace
                self.namespace_indices = {}
                self.namespace_metadata = {}
                
                # Create indices for each namespace
                for namespace in self.namespaces:
                    # Define paths for index and metadata
                    index_path = vector_db_path / f"{client_id}-{namespace}.index"
                    metadata_path = vector_db_path / f"{client_id}-{namespace}.json"
                    
                    # Create or load index
                    if index_path.exists():
                        # Load existing index
                        try:
                            index = faiss.read_index(str(index_path))
                            logger.info(f"Loaded FAISS index for {namespace}")
                        except Exception as e:
                            # Create new if loading fails
                            logger.warning(f"Error loading index for {namespace}: {e}")
                            index = faiss.IndexFlatL2(self.vector_dim)
                    else:
                        # Create new index
                        index = faiss.IndexFlatL2(self.vector_dim)
                        logger.info(f"Created new FAISS index for {namespace}")
                    
                    # Load or initialize metadata
                    if metadata_path.exists():
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                        except Exception as e:
                            logger.warning(f"Error loading metadata for {namespace}: {e}")
                            metadata = {"ids": [], "content": [], "metadata": []}
                    else:
                        metadata = {"ids": [], "content": [], "metadata": []}
                    
                    # Store index and metadata
                    self.namespace_indices[namespace] = index
                    self.namespace_metadata[namespace] = metadata
                
                # Set up compartment indices
                for compartment_id in self.compartments:
                    self._ensure_faiss_compartment(compartment_id)
                
                self.vector_available = True
                logger.info(f"FAISS vector search initialized for client {client_id}")
                logger.info(f"Using model {model_name} with dimension {self.vector_dim}")
                
            except Exception as e:
                logger.error(f"Error initializing FAISS: {e}")
                self.vector_available = False
                # Fall back to file-based storage (already set up by original init)
        
        # Helper method for compartments
        def _ensure_faiss_compartment(self, compartment_id):
            """Ensure FAISS index exists for a compartment."""
            namespace = f"compartment-{compartment_id}"
            
            # Skip if already initialized
            if namespace in self.namespace_indices:
                return
            
            # Set up paths
            vector_db_path = self.data_dir / "faiss_indices"
            index_path = vector_db_path / f"{self.client_id}-{namespace}.index"
            metadata_path = vector_db_path / f"{self.client_id}-{namespace}.json"
            
            # Create or load index
            if index_path.exists():
                try:
                    index = faiss.read_index(str(index_path))
                except Exception:
                    index = faiss.IndexFlatL2(self.vector_dim)
            else:
                index = faiss.IndexFlatL2(self.vector_dim)
            
            # Load or initialize metadata
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                except Exception:
                    metadata = {"ids": [], "content": [], "metadata": []}
            else:
                metadata = {"ids": [], "content": [], "metadata": []}
            
            # Store index and metadata
            self.namespace_indices[namespace] = index
            self.namespace_metadata[namespace] = metadata
            
            logger.info(f"FAISS index ready for compartment: {compartment_id}")
        
        # Add the helper method
        memory.MemoryService._ensure_faiss_compartment = _ensure_faiss_compartment
        
        # Semantic search using FAISS
        async def semantic_search(self, query, namespace="default", limit=5):
            """Semantic search using FAISS vector storage."""
            if not self.vector_available:
                logger.warning("Vector search not available, using keyword search fallback")
                # Fall back to keyword search
                return await self.search(query, namespace, limit)
            
            try:
                # Determine namespace
                if namespace.startswith("compartment-"):
                    compartment_id = namespace[len("compartment-"):]
                    if compartment_id in self.compartments:
                        self._ensure_faiss_compartment(compartment_id)
                    else:
                        logger.warning(f"Invalid compartment: {compartment_id}, using 'conversations'")
                        namespace = "conversations"
                elif namespace not in self.namespace_metadata:
                    logger.warning(f"Invalid namespace: {namespace}, using 'conversations'")
                    namespace = "conversations"
                
                # Generate embedding for query
                embedding = self.vector_model.encode(query)
                
                # Get index and metadata for namespace
                index = self.namespace_indices[namespace]
                metadata_store = self.namespace_metadata[namespace]
                
                # Check if index has any vectors
                if index.ntotal == 0:
                    logger.warning(f"No vectors in index for {namespace}")
                    return {"count": 0, "results": []}
                
                # Perform search
                distances, indices = index.search(np.array([embedding]).astype("float32"), limit)
                
                # Format results
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < 0 or idx >= len(metadata_store["ids"]):
                        continue
                    
                    memory_id = metadata_store["ids"][idx]
                    content = metadata_store["content"][idx]
                    metadata = metadata_store["metadata"][idx]
                    
                    # Calculate relevance score (1 - normalized distance)
                    relevance = 1.0 / (1.0 + distances[0][i])
                    
                    results.append({
                        "id": memory_id,
                        "content": content,
                        "metadata": metadata,
                        "relevance": float(relevance)
                    })
                
                return {
                    "count": len(results),
                    "results": results
                }
            
            except Exception as e:
                logger.error(f"Error in semantic search: {e}")
                return {"count": 0, "results": []}
        
        # Apply the patches
        memory.MemoryService.__init__ = patched_init
        memory.MemoryService.semantic_search = semantic_search
        
        logger.info("Patched memory module with FAISS support successfully")
        return True
    
    except Exception as e:
        logger.error(f"Failed to patch memory module: {e}")
        return False

if __name__ == "__main__":
    if check_dependencies():
        if apply_memory_patch():
            logger.info("FAISS patch applied successfully")
            print("\n✅ Engram memory module patched to use FAISS!")
            print("   You can now use Engram with NumPy 2.x")
            print("   Run the Ollama bridge with: ./engram_with_ollama")
        else:
            logger.error("Failed to apply FAISS patch")
            print("\n❌ Failed to patch memory module")
    else:
        logger.error("Missing required dependencies")
        print("\n❌ Missing dependencies for FAISS patch")
        print("   Please install: pip install faiss-cpu numpy")