#!/usr/bin/env python3
"""
Latent Space Example - Demonstration of latent space reasoning in Engram.

This example shows how to use the latent space reasoning capabilities in Engram
to iteratively refine thoughts and improve problem-solving.
"""

import asyncio
import logging
from typing import Dict, Any, Tuple

from engram.core import LatentInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("latent_example")

# Sample refinement function using iterative thinking
def refine_thought(thought: str) -> Tuple[str, float]:
    """
    Refine a thought by improving it (simulated).
    
    In a real application, this would likely use an LLM to improve the thought.
    For this example, we simply add more details in each iteration.
    
    Args:
        thought: The current thought to refine
        
    Returns:
        Tuple of (refined thought, confidence)
    """
    words = thought.split()
    word_count = len(words)
    
    if "initial" in thought.lower():
        # First refinement
        refined = (
            f"{thought}\n\nUpon further reflection, this solution has several aspects "
            f"that can be improved. First, we should consider the impact on performance. "
            f"Second, we need to evaluate maintainability concerns."
        )
        confidence = 0.4
    elif "further reflection" in thought.lower():
        # Second refinement
        refined = (
            f"{thought}\n\nAfter analyzing performance implications, I've identified "
            f"that we can optimize by implementing caching at strategic points. "
            f"For maintainability, we should apply the strategy pattern to decouple "
            f"the core algorithm from specific implementations."
        )
        confidence = 0.7
    else:
        # Final refinement
        refined = (
            f"{thought}\n\nConcluding my analysis, the optimal solution is to: "
            f"1. Implement the strategy pattern for flexibility "
            f"2. Add LRU caching for frequently accessed data "
            f"3. Create comprehensive documentation "
            f"4. Add thorough unit tests covering edge cases"
        )
        confidence = 0.95
    
    return refined, confidence

async def main():
    """Main example function."""
    logger.info("Initializing Latent Space example")
    
    # Initialize latent interface
    latent = LatentInterface(component_id="example-component")
    
    # Initial thought
    initial_thought = (
        "Initial solution: We could implement this feature using a simple class "
        "with methods for each operation. This would work but might not be optimal."
    )
    
    # Perform iterative thinking
    logger.info("Starting iterative thinking process")
    result = await latent.think_iteratively(
        initial_thought=initial_thought,
        refinement_function=refine_thought,
        max_iterations=5,
        confidence_threshold=0.9,
        metadata={"problem": "feature_implementation", "priority": "high"}
    )
    
    # Display results
    logger.info(f"Thinking completed with {result['iterations']} iterations")
    logger.info(f"Final confidence: {result['confidence']}")
    logger.info("\n--- INITIAL THOUGHT ---\n")
    print(result["initial_thought"])
    logger.info("\n--- FINAL THOUGHT ---\n")
    print(result["final_thought"])
    
    # Retrieve thought with full trace
    thought_id = result["thought_id"]
    logger.info(f"\nRetrieving complete reasoning trace for thought: {thought_id}")
    
    trace = await latent.recall_thinking_process(thought_id, include_iterations=True)
    
    # Display each iteration
    logger.info("\n--- REASONING ITERATIONS ---\n")
    if "iterations" in trace:
        for i, iteration in enumerate(trace["iterations"]):
            print(f"\n[Iteration {i+1}]")
            print(iteration["content"])
            print(f"Confidence: {iteration.get('confidence', 'N/A')}")
    
    # List all thoughts in the space
    all_thoughts = await latent.list_all_thoughts()
    logger.info(f"\nTotal thoughts in latent space: {len(all_thoughts)}")

if __name__ == "__main__":
    asyncio.run(main())