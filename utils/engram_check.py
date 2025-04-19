#!/usr/bin/env python3
"""
Engram Status Checker

This script checks the status of Engram memory services and provides
information about running instances, versions, and memory connectivity.
It can also start, restart, or stop services as needed.

Usage:
  ./engram_check.py                      # Check status only
  ./engram_check.py --start              # Start services if not running
  ./engram_check.py --restart            # Restart services regardless of state
  ./engram_check.py --stop               # Stop running services
  ./engram_check.py --query "test query" # Test memory query
  ./engram_check.py --version-check      # Check for newer versions
"""

import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Check for required dependencies
try:
    import requests
except ImportError:
    print("Error: 'requests' module not found.")
    print("Please install required dependencies with:")
    print("    pip install requests")
    print("or run the install script:")
    print("    ./install.sh")
    sys.exit(1)

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default URLs for services
DEFAULT_HTTP_URL = "http://127.0.0.1:8000/http"
DEFAULT_SERVER_URL = "http://127.0.0.1:8000/memory"
DEFAULT_DATA_DIR = os.path.expanduser("~/.engram")

def get_http_url():
    """Get the HTTP URL for the Engram wrapper."""
    return os.environ.get("ENGRAM_HTTP_URL", DEFAULT_HTTP_URL)

def get_server_url():
    """Get the URL for the Engram memory server."""
    return os.environ.get("ENGRAM_SERVER_URL", DEFAULT_SERVER_URL)

def get_script_path():
    """Get the path to the script directory."""
    return os.path.dirname(os.path.abspath(__file__))

def check_process_running(name_pattern: str) -> List[int]:
    """Check if a process with the given name pattern is running."""
    try:
        # Different command for macOS/Linux vs Windows
        if sys.platform == "win32":
            cmd = ["tasklist", "/FI", f"IMAGENAME eq {name_pattern}"]
        else:
            # Use pgrep for more reliable pattern matching
            result = subprocess.run(["pgrep", "-f", name_pattern], capture_output=True, text=True)
            if result.returncode == 0:
                # pgrep successful, parse the output for PIDs
                pids = [int(pid) for pid in result.stdout.strip().split()]
                return pids
            
            # Fallback to ps aux if pgrep fails
            cmd = ["ps", "aux"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and sys.platform != "win32":  # Ignore error for pgrep fallback
            print(f"{RED}Error checking process status: {result.stderr}{RESET}")
            return []
        
        output = result.stdout
        
        # For Windows, just check if the process is in the output
        if sys.platform == "win32":
            return [1] if name_pattern in output else []
        
        # For macOS/Linux, parse the output to find PIDs
        pids = []
        for line in output.split("\n"):
            if name_pattern in line:
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pids.append(int(parts[1]))
                    except ValueError:
                        pass
        return pids
    except Exception as e:
        print(f"{RED}Error checking process status: {e}{RESET}")
        return []

def check_services() -> Dict[str, Any]:
    """Check if Engram memory services are running."""
    result = {
        "memory_server": {
            "running": False,
            "pid": None,
            "version": None,
            "url": get_server_url(),
        },
        "http_wrapper": {
            "running": False,
            "pid": None,
            "version": None,
            "url": get_http_url(),
        },
        "memory_connected": False,
        "mem0_available": False,
        "vector_available": False,
    }
    
    # Check consolidated server
    consolidated_pids = check_process_running("engram.api.consolidated_server")
    
    if consolidated_pids:
        # If consolidated server is running, both services are available
        result["memory_server"]["running"] = True
        result["memory_server"]["pid"] = consolidated_pids[0]
        result["http_wrapper"]["running"] = True
        result["http_wrapper"]["pid"] = consolidated_pids[0]
    else:
        # Legacy check - look for separate memory server and HTTP wrapper
        memory_pids = check_process_running("engram.api.server")
        
        if memory_pids:
            result["memory_server"]["running"] = True
            result["memory_server"]["pid"] = memory_pids[0]
        
        http_pids = check_process_running("engram.api.http_wrapper")
            
        if http_pids:
            result["http_wrapper"]["running"] = True
            result["http_wrapper"]["pid"] = http_pids[0]
    
    # Try to get version and connectivity information
    if result["http_wrapper"]["running"]:
        try:
            response = requests.get(f"{get_http_url()}/health", timeout=2)
            if response.status_code == 200:
                health_data = response.json()
                result["memory_connected"] = health_data.get("status") == "ok"
                result["mem0_available"] = health_data.get("mem0_available", False)
                result["vector_available"] = health_data.get("vector_available", False)
        except Exception:
            pass
    
    return result

def test_memory_query(query: str = "test") -> Dict[str, Any]:
    """Test a memory query to ensure the memory service is working."""
    result = {
        "success": False,
        "response": None,
        "error": None,
    }
    
    try:
        url = f"{get_http_url()}/query?query={urllib.parse.quote_plus(query)}&namespace=longterm&limit=1"
        with urllib.request.urlopen(url, timeout=5) as response:
            result["success"] = True
            result["response"] = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP error: {e.code}"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def start_services(client_id: str = "claude", data_dir: str = None, force_restart: bool = False) -> bool:
    """Start the Claude Memory Bridge services."""
    # First check if services are already running
    if not force_restart:
        status = check_services()
        if status["memory_server"]["running"] and status["http_wrapper"]["running"]:
            print(f"{YELLOW}Services are already running.{RESET}")
            return True
    
    # Stop services if force_restart is True
    if force_restart:
        stop_services()
    
    # Set up command parameters
    script_path = get_script_path()
    engram_start_path = os.path.join(script_path, "engram_consolidated")
    
    # Make sure the script is executable
    try:
        os.chmod(engram_start_path, 0o755)
    except Exception:
        pass
    
    # Build command
    cmd = [engram_start_path, "--client-id", client_id]
    if data_dir:
        cmd.extend(["--data-dir", data_dir])
    
    # Run the start script
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"{RED}Error starting services: {result.stderr}{RESET}")
            return False
        
        print(f"{GREEN}Services started successfully.{RESET}")
        return True
    except Exception as e:
        print(f"{RED}Error starting services: {e}{RESET}")
        return False

def stop_services() -> bool:
    """Stop the Claude Memory Bridge services."""
    status = check_services()
    
    # Check if services are running
    if not status["memory_server"]["running"] and not status["http_wrapper"]["running"]:
        print(f"{YELLOW}No services are running.{RESET}")
        return True
    
    # Get PIDs
    pids = []
    if status["memory_server"]["running"] and status["memory_server"]["pid"]:
        pids.append(status["memory_server"]["pid"])
    if status["http_wrapper"]["running"] and status["http_wrapper"]["pid"]:
        pids.append(status["http_wrapper"]["pid"])
    
    # Stop processes
    success = True
    for pid in pids:
        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            else:
                subprocess.run(["kill", str(pid)], capture_output=True)
            print(f"{GREEN}Stopped process with PID {pid}.{RESET}")
        except Exception as e:
            print(f"{RED}Error stopping process with PID {pid}: {e}{RESET}")
            success = False
    
    # Give processes time to shut down
    time.sleep(1)
    
    # Verify they're stopped
    status = check_services()
    if status["memory_server"]["running"] or status["http_wrapper"]["running"]:
        print(f"{YELLOW}Warning: Some services are still running after stop attempt.{RESET}")
        success = False
    
    return success

def check_version() -> Dict[str, Any]:
    """Check current version against the latest in the repo."""
    result = {
        "current_version": "Unknown",
        "latest_version": "Unknown",
        "update_available": False,
    }
    
    # Get current version from code
    try:
        script_path = get_script_path()
        version_path = os.path.join(script_path, "engram", "__init__.py")
        with open(version_path, "r") as f:
            version_file = f.read()
            for line in version_file.split("\n"):
                if line.startswith("__version__"):
                    result["current_version"] = line.split("=")[1].strip().strip("'\"")
                    break
    except Exception:
        pass
    
    # Get latest version (in a real implementation, this would check GitHub or PyPI)
    # For now, we'll just report the current version
    result["latest_version"] = result["current_version"]
    
    # In a real implementation, compare versions and set update_available
    # result["update_available"] = parse_version(result["latest_version"]) > parse_version(result["current_version"])
    
    return result

def check_memory_files() -> Dict[str, Any]:
    """Check memory files status and statistics."""
    result = {
        "files_exist": False,
        "client_id": "claude",  # Default
        "memory_count": 0,
        "namespaces": [],
        "last_modified": None,
    }
    
    # Get data directory path
    data_dir = os.environ.get("ENGRAM_DATA_DIR", DEFAULT_DATA_DIR)
    data_path = Path(data_dir)
    
    # Check if directory exists
    if not data_path.exists():
        return result
    
    # Get client ID (looking for client-memories.json files)
    memory_files = list(data_path.glob("*-memories.json"))
    if not memory_files:
        return result
    
    # Use the first file as the main client memory file
    result["files_exist"] = True
    memory_file = memory_files[0]
    result["client_id"] = memory_file.stem.split("-")[0]
    
    # Get file stats
    stat = memory_file.stat()
    result["last_modified"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    
    # Parse the file to get memory statistics
    try:
        with open(memory_file, "r") as f:
            memory_data = json.load(f)
            
            # Extract namespaces and count memories
            total_count = 0
            namespaces = []
            
            for key, values in memory_data.items():
                if isinstance(values, list):
                    count = len(values)
                    total_count += count
                    if count > 0:
                        namespaces.append({"name": key, "count": count})
            
            result["memory_count"] = total_count
            result["namespaces"] = namespaces
    except Exception:
        pass
    
    return result

def display_status_report(services_status: Dict[str, Any], 
                          version_info: Dict[str, Any] = None,
                          memory_files: Dict[str, Any] = None,
                          query_result: Dict[str, Any] = None):
    """Display a comprehensive status report."""
    # Header
    print(f"\n{BOLD}{BLUE}==== Engram Memory Service Status Report ===={RESET}\n")
    
    # Services Status
    print(f"{BOLD}Service Status:{RESET}")
    memory_status = "✅ Running" if services_status["memory_server"]["running"] else "❌ Not Running"
    http_status = "✅ Running" if services_status["http_wrapper"]["running"] else "❌ Not Running"
    mem0_status = "✅ Available" if services_status["mem0_available"] else "❌ Not Available"
    
    print(f"  Memory Server: {memory_status} (PID: {services_status['memory_server']['pid']})")
    print(f"  HTTP Wrapper: {http_status} (PID: {services_status['http_wrapper']['pid']})")
    print(f"  Memory Connection: {'✅ Connected' if services_status['memory_connected'] else '❌ Not Connected'}")
    vector_status = "✅ Available" if services_status["vector_available"] else "❌ Not Available" 
    print(f"  Vector DB Integration: {vector_status}")
    
    # Try to get vector DB version if available
    try:
        from engram.core.memory import VECTOR_DB_NAME, VECTOR_DB_VERSION
        if VECTOR_DB_NAME and VECTOR_DB_VERSION:
            print(f"  Vector DB: {GREEN}{VECTOR_DB_NAME} {VECTOR_DB_VERSION}{RESET}")
        else:
            print(f"  Vector DB: {RED}Not available{RESET}")
    except ImportError:
        print(f"  Vector DB: {RED}Not installed{RESET}")
    except Exception as e:
        print(f"  Vector DB: {YELLOW}Error checking version: {e}{RESET}")
    
    # Version Information
    if version_info:
        print(f"\n{BOLD}Version Information:{RESET}")
        print(f"  Current Version: {version_info['current_version']}")
        print(f"  Latest Version: {version_info['latest_version']}")
        if version_info['update_available']:
            print(f"  {YELLOW}Update Available!{RESET}")
        else:
            print(f"  {GREEN}Up to Date{RESET}")
    
    # Memory Files
    if memory_files:
        print(f"\n{BOLD}Memory Files:{RESET}")
        if memory_files["files_exist"]:
            print(f"  Client ID: {memory_files['client_id']}")
            print(f"  Total Memories: {memory_files['memory_count']}")
            print(f"  Last Modified: {memory_files['last_modified']}")
            print(f"  Active Namespaces:")
            for ns in memory_files["namespaces"]:
                print(f"    - {ns['name']}: {ns['count']} memories")
        else:
            print(f"  {RED}No memory files found.{RESET}")
    
    # Query Test Results
    if query_result:
        print(f"\n{BOLD}Memory Query Test:{RESET}")
        if query_result["success"]:
            response = query_result["response"]
            count = response.get("count", 0)
            print(f"  {GREEN}Query successful!{RESET}")
            print(f"  Results: {count} memory items found")
            
            if count > 0 and "results" in response:
                print(f"  First result: \"{response['results'][0].get('content', '')}\"")
        else:
            print(f"  {RED}Query failed: {query_result['error']}{RESET}")
    
    # Footer
    print(f"\n{BOLD}{BLUE}===================================={RESET}\n")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Engram Memory Status Checker")
    
    # Action arguments
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument("--start", action="store_true", help="Start services if not running")
    action_group.add_argument("--restart", action="store_true", help="Restart services")
    action_group.add_argument("--stop", action="store_true", help="Stop running services")
    
    # Other arguments
    parser.add_argument("--client-id", type=str, default="claude", help="Client ID for memory service")
    parser.add_argument("--data-dir", type=str, default=None, help="Directory to store memory data")
    parser.add_argument("--query", type=str, help="Test a memory query")
    parser.add_argument("--version-check", action="store_true", help="Check for newer versions")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    return parser.parse_args()

def check_interactive():
    """Check if the script is running in an interactive environment."""
    # For Claude, we'll detect if we're in a Jupyter notebook
    try:
        if 'ipykernel' in sys.modules:
            return True
    except:
        pass
    
    # Try to determine if we're in a Claude Code session or other interactive shell
    # This is a heuristic and might not be 100% accurate
    try:
        # Check for Claude-specific environment variables
        if "CLAUDE_API_KEY" in os.environ or "CLAUDE_ENVIRONMENT" in os.environ:
            return True
    except:
        pass
    
    return False

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Check if we're running in Claude
    is_interactive = check_interactive()
    
    # Handle actions
    if args.stop:
        stop_services()
        return
    
    if args.start or args.restart:
        start_services(args.client_id, args.data_dir, args.restart)
        # Give services time to start
        time.sleep(2)
    
    # Check services status
    services_status = check_services()
    
    # Check version if requested
    version_info = check_version() if args.version_check else None
    
    # Check memory files
    memory_files = check_memory_files()
    
    # Test memory query if requested
    query_result = None
    if args.query and services_status["http_wrapper"]["running"]:
        query_result = test_memory_query(args.query)
    
    # Compile full results
    results = {
        "services": services_status,
        "version": version_info,
        "memory_files": memory_files,
        "query_result": query_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    # Output results
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        display_status_report(services_status, version_info, memory_files, query_result)
    
    # If services should be running but aren't, suggest starting them
    if is_interactive and not (services_status["memory_server"]["running"] and services_status["http_wrapper"]["running"]):
        print(f"{YELLOW}Memory services aren't running. Would you like to start them? (y/n){RESET}")
        # For Claude, we'd actually need a way to interact with the user here
        # In a real implementation, this would be more interactive
        print("To start services, use: ./engram_check.py --start")
    
    return results

if __name__ == "__main__":
    main()