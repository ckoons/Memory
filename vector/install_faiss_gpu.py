#!/usr/bin/env python
"""
Script to install FAISS with GPU support
This script detects the appropriate FAISS-GPU package version and installs it
"""

import os
import sys
import subprocess
import platform
import logging
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("install_faiss_gpu")

def detect_cuda_version() -> Optional[str]:
    """Detect CUDA version installed on the system"""
    try:
        # Try nvcc first
        result = subprocess.run(["nvcc", "--version"], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if "release" in line and "V" in line:
                    # Extract version like 11.4 from "release 11.4 V11.4.120"
                    parts = line.split("release")[1].strip().split()
                    if parts:
                        return parts[0].strip()
        
        # Try nvidia-smi as alternative
        result = subprocess.run(["nvidia-smi"], 
                              capture_output=True, text=True, check=False)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if "CUDA Version:" in line:
                    # Extract version like 11.4 from "CUDA Version: 11.4"
                    return line.split("CUDA Version:")[1].strip()
        
        logger.warning("CUDA installation found but couldn't determine version")
        return None
    except Exception as e:
        logger.warning(f"CUDA not detected: {e}")
        return None

def get_compatible_faiss_version(cuda_version: Optional[str] = None) -> str:
    """Get the appropriate FAISS package name based on environment"""
    system = platform.system().lower()
    
    # If no CUDA version detected or not on Linux/Windows, default to CPU
    if not cuda_version or system not in ["linux", "windows"]:
        logger.info("Using FAISS CPU version (GPU support not available)")
        return "faiss-cpu"
    
    # Parse CUDA version to determine FAISS version
    major, minor = 0, 0
    try:
        parts = cuda_version.split(".")
        major = int(parts[0])
        if len(parts) > 1:
            minor = int(parts[1])
    except:
        logger.warning(f"Couldn't parse CUDA version: {cuda_version}")
        return "faiss-cpu"
    
    # FAISS package naming depends on CUDA version
    if major >= 12:
        logger.info(f"Using FAISS for CUDA 12.x (detected: {cuda_version})")
        return "faiss-gpu-cuda12"
    elif major == 11 and minor >= 4:
        logger.info(f"Using FAISS for CUDA 11.x (detected: {cuda_version})")
        return "faiss-gpu-cuda11"
    elif major == 11:
        logger.info(f"Using FAISS for CUDA 11.x (detected: {cuda_version})")
        return "faiss-gpu-cuda11"
    elif major == 10:
        logger.info(f"Using FAISS for CUDA 10.x (detected: {cuda_version})")
        return "faiss-gpu-cuda10"
    else:
        logger.warning(f"CUDA {cuda_version} is not officially supported by FAISS packages")
        logger.info("Defaulting to CPU version")
        return "faiss-cpu"

def install_faiss(package: str) -> bool:
    """Install the specified FAISS package"""
    logger.info(f"Installing {package}...")
    try:
        # Try installing with pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", package],
            capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully installed {package}")
            return True
        else:
            logger.error(f"Failed to install {package}: {result.stderr}")
            
            # Try alternative installation with conda or direct package if available
            if package == "faiss-gpu":
                logger.info("Trying alternative installation methods...")
                # Try installing from conda-forge
                try:
                    conda_result = subprocess.run(
                        ["conda", "install", "-c", "conda-forge", "faiss-gpu", "-y"],
                        capture_output=True, text=True, check=False
                    )
                    if conda_result.returncode == 0:
                        logger.info("Successfully installed faiss-gpu via conda")
                        return True
                except Exception:
                    logger.warning("Conda not available")
            
            # If we get here, installation failed
            return False
    except Exception as e:
        logger.error(f"Error installing {package}: {str(e)}")
        return False

def test_faiss_gpu() -> bool:
    """Test if FAISS GPU is working correctly"""
    logger.info("Testing FAISS GPU installation...")
    
    try:
        # Import FAISS
        import faiss
        logger.info(f"FAISS version: {faiss.__version__}")
        
        # Check if GPU resources are available
        try:
            if faiss.get_num_gpus() > 0:
                logger.info(f"FAISS GPU resources available: {faiss.get_num_gpus()} GPU(s)")
                
                # Create a small test index on GPU
                d = 128  # dimension
                index = faiss.IndexFlatL2(d)  # Create CPU index
                
                # Try to transfer to GPU
                try:
                    res = faiss.StandardGpuResources()
                    gpu_index = faiss.index_cpu_to_gpu(res, 0, index)
                    logger.info("Successfully created GPU index")
                    
                    # Quick test with random vectors
                    import numpy as np
                    vectors = np.random.random((100, d)).astype(np.float32)
                    gpu_index.add(vectors)
                    
                    # Search
                    query = np.random.random((1, d)).astype(np.float32)
                    D, I = gpu_index.search(query, 5)
                    
                    logger.info("FAISS GPU search successful!")
                    return True
                except Exception as e:
                    logger.error(f"Failed to create GPU index: {e}")
                    return False
            else:
                logger.warning("No GPU resources available for FAISS")
                return False
        except Exception as e:
            logger.error(f"Failed to check GPU availability: {e}")
            return False
            
    except ImportError:
        logger.error("Failed to import FAISS")
        return False
    except Exception as e:
        logger.error(f"Error testing FAISS: {e}")
        return False

def main():
    """Main installation function"""
    print("\n--- FAISS GPU Installation Script ---\n")
    
    # Detect CUDA version
    cuda_version = detect_cuda_version()
    if cuda_version:
        logger.info(f"Detected CUDA version: {cuda_version}")
        print(f"\n✅ Detected CUDA version: {cuda_version}")
    else:
        logger.warning("No CUDA installation detected")
        print("\n⚠️ No CUDA installation detected, will install CPU version")
    
    # Get appropriate FAISS package
    faiss_package = get_compatible_faiss_version(cuda_version)
    print(f"\nWill install: {faiss_package}")
    
    # Install FAISS
    if install_faiss(faiss_package):
        print(f"\n✅ Successfully installed {faiss_package}")
        
        # Test GPU functionality if we installed a GPU version
        if "gpu" in faiss_package:
            print("\nTesting GPU functionality...")
            if test_faiss_gpu():
                print("\n✅ FAISS GPU is working correctly")
            else:
                print("\n❌ FAISS GPU installation failed GPU tests, falling back to CPU")
                # Try installing CPU version as fallback
                if install_faiss("faiss-cpu"):
                    print("\n✅ Successfully installed FAISS CPU version as fallback")
                else:
                    print("\n❌ Failed to install CPU fallback")
        
        print("\nInstallation complete!")
    else:
        print(f"\n❌ Failed to install {faiss_package}")
        print("Please check the logs for details")

if __name__ == "__main__":
    main()