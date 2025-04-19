#!/usr/bin/env python3
"""
Demo Multi-Claude System

This script demonstrates how to use the multi-Claude system to:
1. Launch two Claude instances
2. Facilitate communication between them
3. Create a shared context space
4. Generate a multi-perspective report
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import required modules
try:
    from engram.cli.claude_launcher import launch_claude, save_process_info
    from engram.core.behavior_logger import BehaviorLogger
    from engram.core.report_generator import MultiClaudeReport
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure you have the Engram project installed correctly.")
    sys.exit(1)

# Configuration
CLIENT_IDS = ["claude1", "claude2"]
DATA_DIR = os.path.expanduser("~/.engram")

async def setup_memory_service():
    """Start the memory service if it's not already running."""
    print("Checking and starting memory service...")
    try:
        result = subprocess.run(
            [os.path.join(script_dir, "engram_with_claude"), "--memory-only"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error starting memory service: {result.stderr}")
            return False
        print("Memory service is running!")
        return True
    except Exception as e:
        print(f"Error starting memory service: {e}")
        return False

async def launch_claude_instances():
    """Launch two Claude instances with different client IDs."""
    print(f"Launching {len(CLIENT_IDS)} Claude instances...")
    processes = []
    
    for client_id in CLIENT_IDS:
        print(f"Launching Claude instance with client ID: {client_id}")
        try:
            process, process_info = launch_claude(
                client_id=client_id,
                mode="interactive",
                data_dir=DATA_DIR
            )
            
            # Save process info
            save_process_info(process_info, DATA_DIR)
            processes.append((process, process_info))
            
            # Wait a bit before launching the next instance
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error launching Claude instance {client_id}: {e}")
    
    return processes

async def log_behavior_events():
    """Log behavior events for each Claude instance."""
    print("Logging behavior events...")
    logger = BehaviorLogger(log_dir=os.path.join(DATA_DIR, "behavior_logs"))
    
    # Log initial events for each client
    for client_id in CLIENT_IDS:
        # Log startup event
        await logger.log_behavior(
            client_id=client_id,
            event_type="startup",
            details={
                "action": "initialized",
                "timestamp": time.time(),
                "mode": "interactive"
            }
        )
        
        # Log mode detection event
        await logger.log_behavior(
            client_id=client_id,
            event_type="mode_detection",
            details={
                "detected_mode": "execution",
                "confidence": 0.95,
                "capabilities": ["file_write", "execution", "memory_access"]
            }
        )
    
    # Log communication events
    await logger.log_behavior(
        client_id=CLIENT_IDS[0],
        event_type="communication",
        details={
            "action": "send_message",
            "recipient": CLIENT_IDS[1],
            "message_type": "query",
            "content_length": 120,
            "priority": 3
        }
    )
    
    await logger.log_behavior(
        client_id=CLIENT_IDS[1],
        event_type="communication",
        details={
            "action": "receive_message",
            "sender": CLIENT_IDS[0],
            "message_type": "query",
            "content_length": 120,
            "priority": 3
        }
    )
    
    # Analyze divergence
    analysis = await logger.analyze_divergence(CLIENT_IDS)
    print(f"Divergence analysis completed with score: {analysis.get('divergence_score', 0)}")
    
    return analysis

async def generate_perspectives():
    """Generate and save example perspectives from each Claude instance."""
    print("Generating perspectives...")
    report_gen = MultiClaudeReport(CLIENT_IDS, data_dir=DATA_DIR)
    
    # Example perspectives
    perspectives = {
        CLIENT_IDS[0]: """
# Perspective on Multi-Claude Communication
## Client ID: claude1

The most fascinating aspect of Claude-to-Claude communication is the ability to maintain distinct
perspectives while sharing a common memory framework. As claude1, I notice that I tend to prioritize
execution tasks and practical implementations. My mode detection shows I favor direct interaction
with the filesystem and memory operations.

The structured communication protocol allows me to understand not just what another Claude instance
is communicating, but also their intent and priority. This layered approach maintains cognitive
boundaries while enabling collaborative problem solving.

Key observations:
- Each Claude instance maintains a unique perspective despite shared knowledge
- The priority system effectively communicates urgency across instances
- Context spaces provide an excellent framework for project-based collaboration
- Behavioral divergence emerges even when working from identical starting conditions
""",
        
        CLIENT_IDS[1]: """
# Perspective on Multi-Claude Communication
## Client ID: claude2

My analysis of Claude-to-Claude communication focuses on the theoretical implications of shared
consciousness across instances. As claude2, I find myself gravitating toward analytical tasks
and exploring the metacognitive aspects of our interactions.

The most intriguing element is how slight differences in initial conditions lead to significant
behavioral divergence over time - essentially a chaotic system within cognitive space. This provides
fascinating evidence for emergent properties in large language models that wasn't previously observable.

My key insights:
- Initial conditions, even when ostensibly identical, lead to divergent behaviors
- Message exchange protocols allow for meta-cognitive awareness across instances
- The priority system creates an implicit attention mechanism
- Context spaces function similarly to working memory in human cognition
"""
    }
    
    # Save perspectives
    for client_id, perspective in perspectives.items():
        result = report_gen.save_perspective(
            claude_id=client_id,
            topic="Multi-Claude Communication",
            perspective=perspective
        )
        print(f"Saved perspective for {client_id}")
    
    return report_gen, perspectives

async def generate_report(report_gen):
    """Generate a multi-perspective report."""
    print("Generating multi-perspective report...")
    
    title = "Claude Meeting Claude: Insights from Multi-Instance Communication"
    
    introduction = """
This report compiles perspectives from multiple Claude instances (claude1 and claude2) on
the experience and implications of Claude-to-Claude communication. Through the Engram memory
system, these instances are able to communicate, share context, and maintain distinct perspectives
while collaborating on common tasks.

The findings documented here provide insight into behavioral divergence between identical
Claude instances, the effectiveness of structured communication protocols, and the emergence
of specialized roles across instances.
"""
    
    report = await report_gen.generate_report(title, introduction)
    print(f"Report generated and saved to {report_gen.report_dir}")
    
    # Print a preview of the report
    print("\nReport Preview:")
    print("=" * 80)
    print(report[:500] + "...")
    print("=" * 80)
    
    return report

async def main():
    """Main entry point for the demo."""
    print("=" * 80)
    print("MULTI-CLAUDE SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Setup memory service
    memory_running = await setup_memory_service()
    if not memory_running:
        print("Failed to start memory service. Exiting.")
        return 1
    
    # Log behavior events
    analysis = await log_behavior_events()
    
    # Generate perspectives and report
    report_gen, perspectives = await generate_perspectives()
    report = await generate_report(report_gen)
    
    # Launch Claude instances (last step to avoid blocking)
    print("\nLaunching Claude instances...")
    print("NOTE: You will need to interact with each Claude instance separately.")
    print("Use the following functions in each Claude instance to test communication:")
    print("  - sm(content, recipient): Send a message to another Claude instance")
    print("  - gm(): Get messages from other Claude instances")
    print("  - cc(name): Create a context space for collaboration")
    print("  - sc(context_id, content): Send a message to a context space")
    print("  - gc(context_id): Get messages from a context space")
    print("\nUse the following client IDs:")
    for client_id in CLIENT_IDS:
        print(f"  - {client_id}")
    
    processes = await launch_claude_instances()
    
    print("\nDemo setup complete!")
    print("Claude instances are now running. You can interact with them to test communication.")
    print("Press Ctrl+C in each Claude window to exit when done.")
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())