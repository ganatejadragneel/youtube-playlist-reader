import pytest
from pathlib import Path
from unittest.mock import patch
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from src.config.settings import Settings


class TestSettings:
    @pytest.fixture
    def test_settings_class(self):
        """Create a test-specific Settings class that doesn't load .env files."""
        class TestSettings(Settings):
            model_config = SettingsConfigDict(
                env_file=None,  # Don't load .env file
                case_sensitive=False,
            )
        return TestSettings

    def test_settings_with_valid_env_vars(self, mock_env_vars, test_settings_class):
        """Test that settings load correctly with valid environment variables."""
        settings = test_settings_class()
        
        assert str(settings.youtube_url) == mock_env_vars["YOUTUBE_URL"]
        assert settings.youtube_api_key == mock_env_vars["YOUTUBE_API_KEY"]
        assert settings.ollama_base_url == mock_env_vars["OLLAMA_BASE_URL"]
        assert settings.ollama_model == mock_env_vars["OLLAMA_MODEL"]
        assert settings.log_level == mock_env_vars["LOG_LEVEL"]
        
        # Check paths are Path objects
        assert isinstance(settings.data_dir, Path)
        assert isinstance(settings.cache_dir, Path)
        assert isinstance(settings.db_path, Path)
        assert isinstance(settings.vector_db_path, Path)

    def test_settings_with_missing_required_url(self):
        """Test that missing required YouTube URL raises validation error."""
        with patch.dict("os.environ", {"YOUTUBE_URL": ""}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            errors = exc_info.value.errors()
            assert any(error["loc"] == ("youtube_url",) for error in errors)

    def test_settings_with_invalid_youtube_url(self):
        """Test that non-playlist YouTube URL raises validation error."""
        with patch.dict("os.environ", {"YOUTUBE_URL": "https://www.youtube.com/watch?v=123"}, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            errors = exc_info.value.errors()
            assert any("playlist" in str(error["ctx"]["error"]) for error in errors if "ctx" in error)

    def test_ensure_directories_creates_paths(self, temp_dir, mock_env_vars, test_settings_class):
        """Test that ensure_directories creates all necessary directories."""
        settings = test_settings_class()
        settings.ensure_directories()
        
        assert settings.data_dir.exists()
        assert settings.cache_dir.exists()
        assert settings.db_path.parent.exists()
        assert settings.vector_db_path.exists()

    def test_default_values(self):
        """Test that default values are set correctly when env vars are not provided."""
        minimal_env = {"YOUTUBE_URL": "https://www.youtube.com/playlist?list=PLtest"}
        
        with patch.dict("os.environ", minimal_env, clear=True):
            # Create settings without .env file
            from pydantic_settings import SettingsConfigDict
            from src.config.settings import Settings
            
            class TestSettings(Settings):
                model_config = SettingsConfigDict(
                    env_file=None,  # Don't load .env file
                    case_sensitive=False,
                )
            
            settings = TestSettings()
            
            assert settings.youtube_api_key is None
            assert settings.ollama_base_url == "http://localhost:11434"
            assert settings.ollama_model == "llama3.2"
            assert settings.log_level == "INFO"
            assert settings.embedding_model == "all-MiniLM-L6-v2"

    def test_path_conversion_from_string(self):
        """Test that string paths are correctly converted to Path objects."""
        env_vars = {
            "YOUTUBE_URL": "https://www.youtube.com/playlist?list=PLtest",
            "DATA_DIR": "/tmp/custom/data",
            "CACHE_DIR": "/tmp/custom/cache",
        }
        
        with patch.dict("os.environ", env_vars, clear=True):
            settings = Settings()
            
            assert settings.data_dir == Path("/tmp/custom/data")
            assert settings.cache_dir == Path("/tmp/custom/cache")