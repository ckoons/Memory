#!/usr/bin/env python3
"""
Tests for the Memory Service

These tests verify the core functionality of the Engram Memory system's memory service.
"""

import os
import pytest
import tempfile
import asyncio
from pathlib import Path

# Import the memory service
from engram.core.memory_faiss import MemoryService

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def memory_service(temp_data_dir):
    """Create a memory service instance for testing."""
    service = MemoryService(client_id="test", data_dir=temp_data_dir)
    return service

def test_memory_service_init(memory_service):
    """Test that the memory service initializes correctly."""
    assert memory_service is not None
    assert memory_service.client_id == "test"
    assert Path(memory_service.data_dir).exists()

def test_namespaces(memory_service):
    """Test that the memory service has the expected namespaces."""
    namespaces = asyncio.run(memory_service.get_namespaces())
    assert isinstance(namespaces, list)
    assert "conversations" in namespaces
    assert "thinking" in namespaces
    assert "longterm" in namespaces
    assert "projects" in namespaces

def test_add_and_search_memory(memory_service):
    """Test adding and searching for a memory."""
    # Add a memory
    add_result = asyncio.run(memory_service.add(
        content="This is a test memory",
        namespace="conversations",
        metadata={"key": "test_key"}
    ))
    assert add_result is True

    # Search for the memory
    search_result = asyncio.run(memory_service.search(
        query="test memory",
        namespace="conversations",
        limit=5
    ))
    
    assert isinstance(search_result, dict)
    assert "results" in search_result
    assert len(search_result["results"]) == 1
    assert "content" in search_result["results"][0]
    assert "This is a test memory" in search_result["results"][0]["content"]

def test_add_conversation(memory_service):
    """Test adding a conversation."""
    conversation = [
        {"role": "user", "content": "Hello, Claude!"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
        {"role": "user", "content": "I'm testing the memory service."}
    ]
    
    # Add the conversation
    add_result = asyncio.run(memory_service.add(
        content=conversation,
        namespace="conversations"
    ))
    assert add_result is True

    # Search for part of the conversation
    search_result = asyncio.run(memory_service.search(
        query="testing the memory",
        namespace="conversations",
        limit=5
    ))
    
    assert len(search_result["results"]) == 1
    assert "user: I'm testing the memory service." in search_result["results"][0]["content"]

def test_clear_namespace(memory_service):
    """Test clearing a namespace."""
    # Add a memory
    asyncio.run(memory_service.add(
        content="This should be cleared",
        namespace="thinking"
    ))
    
    # Verify it was added
    search_before = asyncio.run(memory_service.search(
        query="cleared",
        namespace="thinking"
    ))
    assert len(search_before["results"]) == 1
    
    # Clear the namespace
    clear_result = asyncio.run(memory_service.clear_namespace("thinking"))
    assert clear_result is True
    
    # Verify it was cleared
    search_after = asyncio.run(memory_service.search(
        query="cleared",
        namespace="thinking"
    ))
    assert len(search_after["results"]) == 0

def test_get_relevant_context(memory_service):
    """Test getting formatted context from multiple namespaces."""
    # Add memories to different namespaces
    asyncio.run(memory_service.add(
        content="Casey likes Python programming",
        namespace="conversations"
    ))
    
    asyncio.run(memory_service.add(
        content="I should remember Casey prefers concise explanations",
        namespace="thinking"
    ))
    
    asyncio.run(memory_service.add(
        content="Casey is working on several AI projects",
        namespace="longterm"
    ))
    
    # Get context for "Casey preferences"
    context = asyncio.run(memory_service.get_relevant_context(
        query="Casey preferences",
        namespaces=["conversations", "thinking", "longterm"],
        limit=2
    ))
    
    assert isinstance(context, str)
    assert "Claude's Memory Context" in context
    assert "Previous Conversations" in context
    assert "Claude's Thoughts" in context
    assert "Important Information" in context
    assert "Casey likes Python" in context
    assert "prefers concise explanations" in context