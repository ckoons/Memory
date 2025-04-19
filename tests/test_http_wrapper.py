#!/usr/bin/env python3
"""
Tests for the HTTP Wrapper API

These tests verify the HTTP API endpoints for the Engram Memory system,
including the enhanced structured memory and Nexus functionality.
"""

import os
import json
import time
import pytest
import tempfile
import asyncio
from pathlib import Path
import threading
import requests
from fastapi.testclient import TestClient
from typing import Dict, List, Any, Optional

# Import the HTTP wrapper
from engram.api.http_wrapper import app, startup_event

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def configured_app(temp_data_dir):
    """Configure the app with a test client ID and data directory."""
    # Set environment variables for the test
    os.environ["ENGRAM_CLIENT_ID"] = "test_client"
    os.environ["ENGRAM_DATA_DIR"] = temp_data_dir
    
    # Initialize the services synchronously instead of using the async startup_event
    from engram.core.memory_faiss import MemoryService
    from engram.core.structured_memory import StructuredMemory
    from engram.core.nexus import NexusInterface
    
    # Update app with test services
    app.memory_service = MemoryService(client_id="test_client", data_dir=temp_data_dir)
    app.structured_memory = StructuredMemory(client_id="test_client", data_dir=temp_data_dir)
    app.nexus = NexusInterface(
        memory_service=app.memory_service,
        structured_memory=app.structured_memory
    )
    app.client_id = "test_client"
    
    return app

@pytest.fixture
def test_client(configured_app):
    """Create a test client for the FastAPI app."""
    client = TestClient(configured_app)
    return client

class TestHTTPWrapper:
    """Test suite for the HTTP Wrapper API."""
    
    def test_root_endpoint(self, test_client):
        """Test the root endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Engram Memory HTTP Wrapper"
    
    def test_health_check(self, test_client):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["client_id"] == "test_client"
        assert "structured_memory_available" in data
        assert "nexus_available" in data
        assert "structured_categories" in data
        assert len(data["structured_categories"]) > 0
    
    def test_store_and_query_memory(self, test_client):
        """Test storing and querying memory."""
        # Store a memory
        response = test_client.get("/store", params={
            "key": "test_key",
            "value": "This is a test memory for API testing",
            "namespace": "conversations"
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Query the memory
        response = test_client.get("/query", params={
            "query": "API testing",
            "namespace": "conversations",
            "limit": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert len(data["results"]) > 0
        assert "This is a test memory for API testing" in data["results"][0]["content"]
    
    def test_thinking_longterm_endpoints(self, test_client):
        """Test the thinking and longterm memory endpoints."""
        # Store a thought
        response = test_client.get("/thinking", params={
            "thought": "I should remember API testing patterns"
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Store longterm memory
        response = test_client.get("/longterm", params={
            "info": "API testing is essential for reliable services"
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Query both
        response = test_client.get("/context", params={
            "query": "API testing",
            "include_thinking": True,
            "limit": 3
        })
        
        assert response.status_code == 200
        context = response.json()["context"]
        assert "Claude's Memory Context" in context
        assert "testing" in context
    
    def test_session_memory(self, test_client):
        """Test writing and loading session memory."""
        # Write session memory
        response = test_client.get("/write", params={
            "content": "Session memory for API testing",
            "metadata": json.dumps({"source": "test_suite"})
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Load session memory
        response = test_client.get("/load", params={"limit": 1})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["content"]) > 0
        assert "Session memory for API testing" in data["content"][0]
        assert len(data["metadata"]) > 0
        assert data["metadata"][0]["source"] == "test_suite"
    
    def test_compartment_endpoints(self, test_client):
        """Test compartment-related endpoints."""
        # Create a compartment
        response = test_client.get("/compartment/create", params={
            "name": "TestCompartment",
            "description": "Test compartment for API testing"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        compartment_id = data["compartment_id"]
        
        # Store in compartment
        response = test_client.get("/compartment/store", params={
            "compartment": compartment_id,
            "content": "Memory stored in test compartment",
            "key": "test_memory"
        })
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # List compartments
        response = test_client.get("/compartment/list")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["compartments"]) > 0
        assert any(c["name"] == "TestCompartment" for c in data["compartments"])
    
    def test_private_memory(self, test_client):
        """Test private memory endpoints."""
        # Store private memory
        response = test_client.get("/private", params={
            "content": "This is a private test memory"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        memory_id = data["memory_id"]
        
        # List private memories
        response = test_client.get("/private/list")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["memories"]) > 0
        
        # Get specific private memory
        response = test_client.get("/private/get", params={"memory_id": memory_id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "This is a private test memory" in data["memory"]["content"]
    
    # Structured Memory API Tests
    
    def test_structured_add_memory(self, test_client):
        """Test adding a structured memory."""
        # Add a structured memory
        response = test_client.get("/structured/add", params={
            "content": "Test structured memory API",
            "category": "projects",
            "importance": 4,
            "tags": json.dumps(["api", "test"]),
            "metadata": json.dumps({"source": "test_suite"})
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data
        memory_id = data["memory_id"]
        
        # Get the memory to verify
        response = test_client.get("/structured/get", params={"memory_id": memory_id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["memory"]["content"] == "Test structured memory API"
        assert data["memory"]["category"] == "projects"
        assert data["memory"]["importance"] == 4
        assert "api" in data["memory"]["tags"]
        assert "test" in data["memory"]["tags"]
    
    def test_structured_auto_categorize(self, test_client):
        """Test adding an auto-categorized memory."""
        # Add auto-categorized memory
        response = test_client.get("/structured/auto", params={
            "content": "My name is Casey and I prefer Python for development"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data
        memory_id = data["memory_id"]
        
        # Get the memory to verify auto-categorization
        response = test_client.get("/structured/get", params={"memory_id": memory_id})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Should be categorized as personal (contains name) or preferences (contains prefer)
        assert data["memory"]["category"] in ["personal", "preferences"]
        assert data["memory"]["importance"] >= 4  # Both categories have high importance
    
    def test_structured_search(self, test_client):
        """Test searching structured memories."""
        # Add a few memories first
        test_client.get("/structured/add", params={
            "content": "Python API testing is important",
            "category": "facts",
            "importance": 3
        })
        
        test_client.get("/structured/add", params={
            "content": "Always test HTTP endpoints thoroughly",
            "category": "preferences",
            "importance": 4
        })
        
        # Search by query
        response = test_client.get("/structured/search", params={
            "query": "test",
            "min_importance": 3,
            "limit": 10,
            "sort_by": "importance"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] >= 2
        
        # Search by category
        response = test_client.get("/structured/search", params={
            "categories": json.dumps(["facts"]),
            "min_importance": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] >= 1
        assert data["results"][0]["category"] == "facts"
    
    def test_structured_digest(self, test_client):
        """Test getting a memory digest."""
        # Add some memories first
        test_client.get("/structured/add", params={
            "content": "Important API design principle: consistency",
            "category": "facts",
            "importance": 5
        })
        
        test_client.get("/structured/add", params={
            "content": "Testing HTTP endpoints requires careful status code checks",
            "category": "projects",
            "importance": 4
        })
        
        # Get a digest
        response = test_client.get("/structured/digest", params={
            "max_memories": 10,
            "include_private": False
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "digest" in data
        digest = data["digest"]
        
        assert "Memory Digest" in digest
        assert "Facts" in digest
        assert "Important API design principle" in digest
        assert "Projects" in digest
        assert "Testing HTTP endpoints" in digest
    
    def test_structured_context(self, test_client):
        """Test getting context memories."""
        # Add memories first
        test_client.get("/structured/add", params={
            "content": "FastAPI is a great framework for building APIs",
            "category": "facts",
            "importance": 3
        })
        
        test_client.get("/structured/add", params={
            "content": "Always test API endpoints with proper error handling",
            "category": "preferences",
            "importance": 4
        })
        
        # Get context memories
        response = test_client.get("/structured/context", params={
            "text": "I'm building an API with FastAPI and need testing approaches",
            "max_memories": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memories" in data
        assert len(data["memories"]) > 0
        
        # At least one memory should mention API
        found_api = False
        for memory in data["memories"]:
            if "API" in memory["content"]:
                found_api = True
                break
                
        assert found_api, "No API-related memory found in context"
    
    # Nexus API Tests
    
    def test_nexus_endpoints(self, test_client):
        """Test Nexus interface endpoints."""
        # Start a Nexus session
        response = test_client.get("/nexus/start", params={"session_name": "API Test Session"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "Nexus Session Started" in data["message"]
        assert "API Test Session" in data["message"]
        
        # Process a user message
        response = test_client.get("/nexus/process", params={
            "message": "Let's discuss API testing with structured memory",
            "is_user": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Store a memory through Nexus
        response = test_client.get("/nexus/store", params={
            "content": "Nexus API endpoints should be thoroughly tested",
            "category": "projects",
            "importance": 4,
            "tags": json.dumps(["api", "testing"]),
            "metadata": json.dumps({"source": "test_suite"})
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
        assert "structured_memory_id" in data["result"]
        
        # Search memories through Nexus
        response = test_client.get("/nexus/search", params={
            "query": "Nexus API",
            "min_importance": 3,
            "limit": 5
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert "combined" in data["results"]
        assert len(data["results"]["combined"]) > 0
        
        # End the Nexus session
        response = test_client.get("/nexus/end", params={
            "summary": "Successfully tested Nexus API endpoints"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "Session ended" in data["message"]
        assert "Successfully tested" in data["message"]


if __name__ == "__main__":
    pytest.main(["-xvs", "test_http_wrapper.py"])