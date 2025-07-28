from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl, field_validator, model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # YouTube Configuration - can be either playlist or channel URL
    youtube_url: HttpUrl  # Changed from youtube_playlist_url to support both
    youtube_api_key: Optional[str] = None

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # Application Configuration
    log_level: str = "INFO"
    data_dir: Path = Path("./data")
    cache_dir: Path = Path("./data/cache")
    db_path: Path = Path("./data/db/youtube_reader.db")

    # Vector Database Configuration
    vector_db_path: Path = Path("./data/db/chroma")
    embedding_model: str = "all-MiniLM-L6-v2"

    @field_validator("data_dir", "cache_dir", "db_path", "vector_db_path", mode="before")
    @classmethod
    def ensure_path(cls, v: str) -> Path:
        return Path(v)

    @field_validator("youtube_url", mode="before")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("YouTube URL is required")
        
        # Accept both playlist and channel URLs
        is_playlist = "playlist" in v or "list=" in v
        is_channel = any(pattern in v for pattern in [
            "youtube.com/channel/",
            "youtube.com/c/",
            "youtube.com/user/",
            "youtube.com/@"
        ])
        
        if not (is_playlist or is_channel):
            raise ValueError("URL must be a YouTube playlist or channel URL")
        return v

    @model_validator(mode="after")
    def convert_empty_strings_to_none(self):
        if self.youtube_api_key == "":
            self.youtube_api_key = None
        return self

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()