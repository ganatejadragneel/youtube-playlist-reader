import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
import os


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars(temp_dir):
    """Mock environment variables for testing."""
    env_vars = {
        "YOUTUBE_PLAYLIST_URL": "https://www.youtube.com/playlist?list=PLtest123",
        "YOUTUBE_API_KEY": "test_api_key",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3.2",
        "LOG_LEVEL": "DEBUG",
        "DATA_DIR": str(temp_dir / "data"),
        "CACHE_DIR": str(temp_dir / "cache"),
        "DB_PATH": str(temp_dir / "db" / "test.db"),
        "VECTOR_DB_PATH": str(temp_dir / "vector_db"),
        "EMBEDDING_MODEL": "test-model",
    }
    
    with patch.dict(os.environ, env_vars, clear=True):
        yield env_vars