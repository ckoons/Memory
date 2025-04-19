#!/usr/bin/env python3
"""
Tests for the Shared Latent Space adapter with Hermes integration.

This module tests the SharedLatentSpace class that enables cross-component
sharing of reasoning insights via Hermes services.
"""

import asyncio
import pytest
import os
import shutil
import tempfile
import json
from unittest.mock import patch, MagicMock

# Import the class to test
from engram.integrations.hermes.latent_space_adapter import SharedLatentSpace


# Mock Hermes services for testing
class MockMessageBus:
    def __init__(self):
        self.messages = []
        self.subscriptions = {}
        
    async def start(self):
        return True
        
    async def publish(self, topic, message, metadata=None):
        self.messages.append({
            "topic": topic,
            "content": message,
            "metadata": metadata or {}
        })
        
        # Call handlers for this topic
        handlers = self.subscriptions.get(topic, [])
        for handler in handlers:
            msg = {
                "topic": topic, 
                "content": message,
                "metadata": metadata or {}
            }
            await handler(msg)
        
        return True
        
    async def subscribe(self, topic, handler):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(handler)
        return True
        
    async def close(self):
        return True


class MockMemoryService:
    def __init__(self):
        self.memories = []
        self.search_results = []
        
    async def add(self, content, namespace, metadata=None):
        self.memories.append({
            "content": content,
            "namespace": namespace,
            "metadata": metadata or {}
        })
        return True
        
    async def search(self, query, namespace, limit=10):
        # Return predefined results or empty list
        return {
            "results": self.search_results[:limit] if self.search_results else [],
            "count": len(self.search_results) if self.search_results else 0
        }
        
    async def close(self):
        return True


@pytest.fixture
def mock_hermes():
    """Create mock Hermes services."""
    message_bus = MockMessageBus()
    memory_service = MockMemoryService()
    
    # Create patcher for MessageBusAdapter
    message_bus_patcher = patch(
        "engram.integrations.hermes.latent_space_adapter.MessageBusAdapter",
        return_value=message_bus
    )
    
    # Create patcher for HermesMemoryService
    memory_service_patcher = patch(
        "engram.integrations.hermes.latent_space_adapter.HermesMemoryService",
        return_value=memory_service
    )
    
    # Start patchers
    message_bus_patcher.start()
    memory_service_patcher.start()
    
    # Set HAS_HERMES to True
    has_hermes_patcher = patch(
        "engram.integrations.hermes.latent_space_adapter.HAS_HERMES",
        True
    )
    has_hermes_patcher.start()
    
    yield {
        "message_bus": message_bus,
        "memory_service": memory_service
    }
    
    # Stop patchers
    message_bus_patcher.stop()
    memory_service_patcher.stop()
    has_hermes_patcher.stop()


@pytest.fixture
async def shared_latent_space(mock_hermes):
    """Create a temporary shared latent space for testing."""
    # Create temporary directory for test data
    test_dir = tempfile.mkdtemp()
    
    # Create shared latent space
    sls = SharedLatentSpace(
        component_id="test_component",
        namespace="test_namespace",
        data_dir=test_dir
    )
    
    # Start the service
    await sls.start()
    
    yield sls
    
    # Clean up
    await sls.close()
    shutil.rmtree(test_dir)


@pytest.mark.asyncio
async def test_initialize_shared_latent_space(shared_latent_space, mock_hermes):
    """Test initializing a shared latent space."""
    # Verify initialization
    assert shared_latent_space.component_id == "test_component"
    assert shared_latent_space.namespace == "test_namespace"
    assert shared_latent_space.shared_insights is True
    assert shared_latent_space.shared_topic == "tekton.latent_space.test_namespace"
    
    # Verify Hermes services were initialized
    assert shared_latent_space.hermes_available is True
    assert shared_latent_space.message_bus is not None
    assert shared_latent_space.memory_service is not None


@pytest.mark.asyncio
async def test_share_insight(shared_latent_space, mock_hermes):
    """Test sharing an insight with other components."""
    # Initialize a thought
    thought_id = await shared_latent_space.initialize_thought(
        "This is a test thought for sharing insights."
    )
    
    # Share the insight
    summary = "Test insight summary"
    insight = await shared_latent_space.share_insight(thought_id, summary)
    
    # Verify the insight was created
    assert insight is not None
    assert insight["thought_id"] == thought_id
    assert insight["summary"] == summary
    assert insight["namespace"] == "test_namespace"
    
    # Verify it was published to the message bus
    message_bus = mock_hermes["message_bus"]
    assert len(message_bus.messages) > 0
    
    # Find the relevant message
    insight_message = None
    for msg in message_bus.messages:
        if msg["topic"] == shared_latent_space.shared_topic:
            insight_message = msg
            break
    
    assert insight_message is not None
    assert insight_message["content"]["thought_id"] == thought_id
    assert insight_message["content"]["summary"] == summary
    assert insight_message["metadata"]["component"] == "test_component"
    
    # Verify it was stored in memory service
    memory_service = mock_hermes["memory_service"]
    assert len(memory_service.memories) > 0
    
    # Find the relevant memory
    insight_memory = None
    for mem in memory_service.memories:
        if mem["namespace"] == "latent_insights":
            insight_memory = mem
            break
    
    assert insight_memory is not None
    assert insight_memory["content"].startswith("LATENT INSIGHT:")
    assert insight_memory["metadata"]["thought_id"] == thought_id
    assert insight_memory["metadata"]["component"] == "test_component"


@pytest.mark.asyncio
async def test_receive_insight(shared_latent_space, mock_hermes):
    """Test receiving an insight from another component."""
    # Create a handler to track received insights
    received_insights = []
    
    async def insight_handler(insight):
        received_insights.append(insight)
    
    # Register the handler
    await shared_latent_space.register_insight_handler(insight_handler)
    
    # Simulate receiving an insight via message bus
    message_bus = mock_hermes["message_bus"]
    await message_bus.publish(
        topic=shared_latent_space.shared_topic,
        message={
            "thought_id": "external_thought_123",
            "summary": "External component insight",
            "iteration": 2,
            "finalized": True,
            "namespace": "test_namespace"
        },
        metadata={
            "component": "other_component",
            "insight_type": "latent_space",
            "timestamp": 1234567890
        }
    )
    
    # Give the handler time to process
    await asyncio.sleep(0.1)
    
    # Verify the insight was received and handler was called
    assert len(received_insights) > 0
    
    # Verify the insight data
    insight = received_insights[0]
    assert insight["source_component"] == "other_component"
    assert insight["thought_id"] == "external_thought_123"
    assert insight["summary"] == "External component insight"


@pytest.mark.asyncio
async def test_get_recent_insights(shared_latent_space, mock_hermes):
    """Test retrieving recent insights."""
    # Set up mock search results
    memory_service = mock_hermes["memory_service"]
    memory_service.search_results = [
        {
            "metadata": {
                "component": "component_1",
                "thought_id": "thought_1",
                "namespace": "test_namespace",
                "timestamp": 1234567890,
                "insight": json.dumps({
                    "summary": "Insight 1",
                    "iteration": 1,
                    "finalized": False
                })
            }
        },
        {
            "metadata": {
                "component": "component_2",
                "thought_id": "thought_2",
                "namespace": "test_namespace",
                "timestamp": 1234567891,
                "insight": json.dumps({
                    "summary": "Insight 2",
                    "iteration": 2,
                    "finalized": True
                })
            }
        },
        {
            "metadata": {
                "component": "test_component",  # From our component
                "thought_id": "thought_3",
                "namespace": "test_namespace",
                "timestamp": 1234567892,
                "insight": json.dumps({
                    "summary": "Insight 3",
                    "iteration": 1,
                    "finalized": False
                })
            }
        }
    ]
    
    # Get insights excluding own
    insights = await shared_latent_space.get_recent_insights(include_own=False)
    
    # Verify 2 insights returned (excluding our own)
    assert len(insights) == 2
    
    # Verify correct ordering (newest first)
    assert insights[0]["thought_id"] == "thought_2"
    assert insights[1]["thought_id"] == "thought_1"
    
    # Get insights including own
    insights_with_own = await shared_latent_space.get_recent_insights(include_own=True)
    
    # Verify all 3 insights returned
    assert len(insights_with_own) == 3
    assert insights_with_own[0]["thought_id"] == "thought_3"  # Our own insight


if __name__ == "__main__":
    asyncio.run(pytest.main(["-xvs", __file__]))