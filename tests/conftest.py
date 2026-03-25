"""Test fixtures for CalSync API tests."""
import os
import pytest
from unittest.mock import Mock, MagicMock
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app configured for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['DEBUG'] = False
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock Supabase client for tests."""
    mock_client = MagicMock()

    # Mock table operations
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Default successful response
    mock_response = MagicMock()
    mock_response.data = []

    # Chain methods for fluent API
    mock_table.insert.return_value.execute.return_value = mock_response
    mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
    mock_table.update.return_value.eq.return_value.execute.return_value = mock_response
    mock_table.delete.return_value.eq.return_value.execute.return_value = mock_response

    # Patch the supabase client in calsync module
    from src import calsync
    monkeypatch.setattr(calsync, 'supabase', mock_client)

    return mock_client


@pytest.fixture
def sample_event():
    """Sample event data for testing."""
    return {
        "title": "Test Meeting",
        "start": "2024-12-25T10:00:00Z",
        "end": "2024-12-25T11:00:00Z",
        "description": "Test description",
        "location": "Test location"
    }


@pytest.fixture
def mock_api_key():
    """Mock API key for testing."""
    return "csk_test123456789012345678"


@pytest.fixture
def mock_api_key_data():
    """Mock API key data from database."""
    return {
        "api_key": "csk_test123456789012345678",
        "plan": "free",
        "usage_count": 0,
        "bubble_app_id": "test_app"
    }


@pytest.fixture
def mock_pro_api_key_data():
    """Mock Pro API key data from database."""
    return {
        "api_key": "csk_pro123456789012345678",
        "plan": "pro",
        "usage_count": 5,
        "bubble_app_id": "test_app_pro"
    }
