#!/usr/bin/env python3
"""
Tests for the Latent Space Memory system.

This module contains tests for the LatentMemorySpace class to ensure
proper functionality of the continuous latent space reasoning framework.
"""

import asyncio
import pytest
import os
import shutil
import tempfile
from engram.core.latent_space import LatentMemorySpace, ConvergenceDetector


@pytest.fixture
async def latent_space():
    """Create a temporary latent space for testing."""
    # Create temporary directory for test data
    test_dir = tempfile.mkdtemp()
    
    # Create latent space
    ls = LatentMemorySpace(
        component_id="test_component",
        namespace="test_namespace",
        data_dir=test_dir
    )
    
    yield ls
    
    # Clean up
    shutil.rmtree(test_dir)


@pytest.mark.asyncio
async def test_initialize_thought(latent_space):
    """Test initializing a thought in latent space."""
    thought_seed = "Initial thought about latent space reasoning."
    metadata = {"category": "test", "priority": "high"}
    
    thought_id = await latent_space.initialize_thought(thought_seed, metadata)
    
    # Verify thought was created
    assert thought_id is not None
    assert thought_id.startswith("thought_")
    
    # Get the thought
    thought = latent_space.thoughts[thought_id]
    
    # Verify content and metadata
    assert thought["content"] == thought_seed
    assert thought["metadata"]["category"] == "test"
    assert thought["metadata"]["priority"] == "high"
    assert thought["metadata"]["component_id"] == "test_component"
    assert thought["metadata"]["namespace"] == "test_namespace"
    assert thought["metadata"]["iteration"] == 0
    assert thought["metadata"]["finalized"] is False
    
    # Verify iteration tracking
    assert latent_space.iterations[thought_id] == 0
    assert len(thought["iterations"]) == 1
    assert thought["iterations"][0]["content"] == thought_seed


@pytest.mark.asyncio
async def test_refine_thought(latent_space):
    """Test refining a thought through multiple iterations."""
    # Initialize thought
    thought_id = await latent_space.initialize_thought("Initial thought.")
    
    # First refinement
    refinement1 = "Refined thought with additional details."
    await latent_space.refine_thought(thought_id, refinement1)
    
    # Verify refinement
    thought = latent_space.thoughts[thought_id]
    assert thought["content"] == refinement1
    assert thought["metadata"]["iteration"] == 1
    assert len(thought["iterations"]) == 2
    
    # Second refinement with metadata
    refinement2 = "Further refined thought with even more insight."
    metadata_updates = {"confidence": 0.8}
    await latent_space.refine_thought(
        thought_id, 
        refinement2,
        metadata_updates=metadata_updates
    )
    
    # Verify second refinement
    thought = latent_space.thoughts[thought_id]
    assert thought["content"] == refinement2
    assert thought["metadata"]["iteration"] == 2
    assert thought["metadata"]["confidence"] == 0.8
    assert len(thought["iterations"]) == 3


@pytest.mark.asyncio
async def test_finalize_thought(latent_space):
    """Test finalizing a thought and persisting it."""
    # Initialize thought
    thought_id = await latent_space.initialize_thought("Initial thought.")
    
    # Refine
    await latent_space.refine_thought(thought_id, "Refined thought.")
    
    # Finalize with new content
    final_content = "Final version of the thought."
    final_metadata = {"final_score": 9.5}
    
    finalized = await latent_space.finalize_thought(
        thought_id,
        final_content=final_content,
        persist=True,
        metadata_updates=final_metadata
    )
    
    # Verify finalization
    assert finalized["content"] == final_content
    assert finalized["metadata"]["finalized"] is True
    assert finalized["metadata"]["final_score"] == 9.5
    assert "finalized_at" in finalized["metadata"]
    
    # Verify iterations
    assert len(finalized["iterations"]) == 3  # Initial + refinement + final
    assert finalized["iterations"][-1]["content"] == final_content
    assert finalized["iterations"][-1]["is_final"] is True
    
    # Verify persistence
    file_path = os.path.join(latent_space.data_dir, f"{thought_id}.json")
    assert os.path.exists(file_path)
    
    # Verify we can't refine a finalized thought
    with pytest.raises(ValueError) as excinfo:
        await latent_space.refine_thought(thought_id, "Cannot refine after finalization.")
    assert "finalized thought" in str(excinfo.value)


@pytest.mark.asyncio
async def test_get_reasoning_trace(latent_space):
    """Test retrieving a reasoning trace with and without iterations."""
    # Initialize and refine a thought multiple times
    thought_id = await latent_space.initialize_thought("Initial seed.")
    await latent_space.refine_thought(thought_id, "First refinement.")
    await latent_space.refine_thought(thought_id, "Second refinement.")
    await latent_space.finalize_thought(thought_id, "Final version.")
    
    # Get trace without iterations
    trace_simple = await latent_space.get_reasoning_trace(thought_id, include_iterations=False)
    
    # Should include only first and last iteration
    assert len(trace_simple["iterations"]) == 2
    assert trace_simple["iterations"][0]["content"] == "Initial seed."
    assert trace_simple["iterations"][1]["content"] == "Final version."
    
    # Get full trace
    trace_full = await latent_space.get_reasoning_trace(thought_id, include_iterations=True)
    
    # Should include all iterations
    assert len(trace_full["iterations"]) == 4  # Initial + 2 refinements + final
    assert trace_full["iterations"][0]["content"] == "Initial seed."
    assert trace_full["iterations"][1]["content"] == "First refinement."
    assert trace_full["iterations"][2]["content"] == "Second refinement."
    assert trace_full["iterations"][3]["content"] == "Final version."


@pytest.mark.asyncio
async def test_convergence_detector():
    """Test the convergence detection functionality."""
    # Test text similarity
    sim1 = await ConvergenceDetector.text_similarity(
        "This is a test of the convergence detector.",
        "This is a test of the similarity function."
    )
    assert 0.5 < sim1 < 1.0  # Should be somewhat similar
    
    sim2 = await ConvergenceDetector.text_similarity(
        "This is a test of the convergence detector.",
        "Completely unrelated content with no shared words."
    )
    assert sim2 < 0.3  # Should have low similarity
    
    # Test convergence detection
    iterations = [
        {"content": "Initial thought about AI systems."},
        {"content": "Refined thought about artificial intelligence systems."},
        {"content": "Detailed analysis of artificial intelligence systems and capabilities."},
        {"content": "Detailed analysis of artificial intelligence systems and their capabilities."}
    ]
    
    # Should not detect convergence with default threshold (iterations still changing)
    not_converged = await ConvergenceDetector.detect_convergence(iterations[:3])
    assert not not_converged
    
    # Should detect convergence (last two iterations very similar)
    converged = await ConvergenceDetector.detect_convergence(iterations, threshold=0.7)
    assert converged


@pytest.mark.asyncio
async def test_delete_thought(latent_space):
    """Test deleting a thought from latent space."""
    # Initialize and persist a thought
    thought_id = await latent_space.initialize_thought("Test thought for deletion.")
    await latent_space.finalize_thought(thought_id, persist=True)
    
    # Verify it exists
    file_path = os.path.join(latent_space.data_dir, f"{thought_id}.json")
    assert os.path.exists(file_path)
    assert thought_id in latent_space.thoughts
    
    # Delete it
    result = await latent_space.delete_thought(thought_id)
    
    # Verify deletion
    assert result is True
    assert thought_id not in latent_space.thoughts
    assert thought_id not in latent_space.iterations
    assert not os.path.exists(file_path)


@pytest.mark.asyncio
async def test_clear_namespace(latent_space):
    """Test clearing all thoughts in a namespace."""
    # Create multiple thoughts
    thought_ids = []
    for i in range(5):
        thought_id = await latent_space.initialize_thought(f"Thought {i}")
        await latent_space.finalize_thought(thought_id, persist=True)
        thought_ids.append(thought_id)
    
    # Verify they exist
    for thought_id in thought_ids:
        assert thought_id in latent_space.thoughts
        file_path = os.path.join(latent_space.data_dir, f"{thought_id}.json")
        assert os.path.exists(file_path)
    
    # Clear namespace
    count = await latent_space.clear_namespace()
    
    # Verify clearing
    assert count == 5
    assert len(latent_space.thoughts) == 0
    assert len(latent_space.iterations) == 0
    
    # Check files are gone
    for thought_id in thought_ids:
        file_path = os.path.join(latent_space.data_dir, f"{thought_id}.json")
        assert not os.path.exists(file_path)


if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", __file__]))