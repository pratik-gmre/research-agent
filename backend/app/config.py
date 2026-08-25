"""Central configuration, loaded from environment variables / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"

    embedding_model: str = "intfloat/multilingual-e5-large"
    ocr_languages: str = "eng+nep"

    raw_data_dir: str = "./data/raw"
    chroma_persist_dir: str = "./data/chroma"

    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 200

    top_k: int = 10


settings = Settings()
