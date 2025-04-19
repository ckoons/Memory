#!/usr/bin/env python3
"""
Tests for the QuickMem module with Structured Memory and Nexus features

These tests verify the functionality of the QuickMem module with
the enhanced structured memory and Nexus capabilities.
"""

import os
import json
import pytest
import tempfile
import asyncio
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import quickmem module
from engram.cli.quickmem import (
    memory_digest, start_nexus, process_message, auto_remember, end_nexus
)

@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response for testing."""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
            
        def read(self):
            return json.dumps(self.json_data).encode()
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    return MockResponse

class TestQuickMemWithStructuredMemory:
    """Test suite for QuickMem with structured memory and Nexus features."""
    
    @pytest.mark.asyncio
    @patch('urllib.request.urlopen')
    async def test_memory_digest(self, mock_urlopen, mock_http_response):
        """Test the memory_digest function."""
        # Mock response for the digest endpoint
        digest_data = {
            "success": True,
            "digest": """# Memory Digest

## Personal
- ★★★★★ Casey is a software engineer (2025-03-15)
- ★★★★ Casey prefers Python for development (2025-03-15)

## Projects
- ★★★★★ Working on Engram Memory system (2025-03-15)
- ★★★★ Engram uses structured storage with FAISS (2025-03-15)
"""
        }
        
        mock_urlopen.return_value = mock_http_response(digest_data)
        
        # Call memory_digest function
        digest = await memory_digest(max_memories=10, include_private=False)
        
        # Verify the function returned the expected digest
        assert digest is not None
        assert "Memory Digest" in digest
        assert "Casey is a software engineer" in digest
        assert "Working on Engram Memory system" in digest
        
        # Verify the correct URL was called
        mock_urlopen.assert_called_once()
        url = mock_urlopen.call_args[0][0]
        assert "/structured/digest" in url
        assert "max_memories=10" in url
        assert "include_private=False" in url
    
    @pytest.mark.asyncio
    @patch('urllib.request.urlopen')
    async def test_start_nexus(self, mock_urlopen, mock_http_response):
        """Test the start_nexus function."""
        # Mock response for the nexus start endpoint
        start_data = {
            "success": True,
            "session_id": "session-1234567890",
            "message": """# Nexus Session Started

Session: Test Session (ID: session-1234567890)

# Memory Digest

## Personal
- ★★★★★ Casey is a software engineer (2025-03-15)

## Projects
- ★★★★★ Working on Engram Memory system (2025-03-15)
"""
        }
        
        mock_urlopen.return_value = mock_http_response(start_data)
        
        # Call start_nexus function
        message = await start_nexus(session_name="Test Session")
        
        # Verify the function returned the expected message
        assert message is not None
        assert "Nexus Session Started" in message
        assert "Test Session" in message
        assert "Memory Digest" in message
        
        # Verify the correct URL was called
        mock_urlopen.assert_called_once()
        url = mock_urlopen.call_args[0][0]
        assert "/nexus/start" in url
        # Test Session is URL encoded as Test+Session, so we check for session_name=Test
        assert "session_name=Test" in url
    
    @pytest.mark.asyncio
    @patch('urllib.request.urlopen')
    async def test_process_message(self, mock_urlopen, mock_http_response):
        """Test the process_message function."""
        # Mock response for the nexus process endpoint
        process_data = {
            "success": True,
            "result": """### Relevant Memory Context

#### Projects
- ★★★★★ Working on Engram Memory system (2025-03-15)
- ★★★★ Engram uses structured storage with FAISS (2025-03-15)

Let's discuss the Engram Memory system project"""
        }
        
        mock_urlopen.return_value = mock_http_response(process_data)
        
        # Call process_message function
        result = await process_message(
            message="Let's discuss the Engram Memory system project",
            is_user=True
        )
        
        # Verify the function returned the expected result
        assert result is not None
        assert "Relevant Memory Context" in result
        assert "Projects" in result
        assert "Working on Engram Memory system" in result
        
        # Verify the correct URL was called
        mock_urlopen.assert_called_once()
        url = mock_urlopen.call_args[0][0]
        assert "/nexus/process" in url
        assert "is_user=True" in url
    
    @pytest.mark.asyncio
    @patch('urllib.request.urlopen')
    async def test_auto_remember(self, mock_urlopen, mock_http_response):
        """Test the auto_remember function."""
        # Mock response for the structured/auto endpoint
        auto_data = {
            "success": True,
            "memory_id": "personal-1234567890-1234"
        }
        
        mock_urlopen.return_value = mock_http_response(auto_data)
        
        # Call auto_remember function
        memory_id = await auto_remember(
            content="I prefer using Python for development projects"
        )
        
        # Verify the function returned the expected memory ID
        assert memory_id is not None
        assert memory_id == "personal-1234567890-1234"
        
        # Verify the correct URL was called
        mock_urlopen.assert_called_once()
        url = mock_urlopen.call_args[0][0]
        assert "/structured/auto" in url
        assert "content=" in url
    
    @pytest.mark.asyncio
    @patch('urllib.request.urlopen')
    async def test_end_nexus(self, mock_urlopen, mock_http_response):
        """Test the end_nexus function."""
        # Mock response for the nexus end endpoint
        end_data = {
            "success": True,
            "message": "Session ended. Successfully completed the test session with 5 messages exchanged."
        }
        
        mock_urlopen.return_value = mock_http_response(end_data)
        
        # Call end_nexus function
        message = await end_nexus(
            summary="Successfully completed the test session"
        )
        
        # Verify the function returned the expected message
        assert message is not None
        assert "Session ended" in message
        assert "Successfully completed" in message
        
        # Verify the correct URL was called
        mock_urlopen.assert_called_once()
        url = mock_urlopen.call_args[0][0]
        assert "/nexus/end" in url
        assert "summary=" in url


if __name__ == "__main__":
    pytest.main(["-xvs", "test_quickmem.py"])