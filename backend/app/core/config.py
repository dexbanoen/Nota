from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/nota.db"
    chroma_path: str = "./data/chroma"
    chroma_collection_name: str = "nota_chunks"
    ollama_base_url: str = "http://localhost:11434"
    ollama_llm_model: str = "llama3.1:latest"
    ollama_embedding_model: str = "nomic-embed-text"
    pdf_storage_path: str = "../storage/pdfs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
