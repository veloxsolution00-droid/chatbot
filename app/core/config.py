from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    generation_model: str = "gemma2:2b"
    embedding_model: str = "nomic-embed-text"

    # All durable application data lives below data/ by default.
    data_path: Path = ROOT / "data"
    uploads_path: Path | None = None
    extracted_path: Path | None = None
    chroma_path: Path | None = None
    metadata_path: Path | None = None
    logs_path: Path | None = None
    jobs_path: Path | None = None
    sqlite_path: Path | None = None

    collection_name: str = "document_chunks"
    chunk_size: int = 1800
    chunk_overlap: int = 300
    top_k: int = 1
    retrieval_candidate_multiplier: int = 5
    embedding_batch_size: int = 16
    min_similarity: float = 0.25
    max_file_mb: int = 100
    max_batch_mb: int = 500
    max_upload_files: int = 50
    ingestion_workers: int = 1
    inference_concurrency: int = 1
    admin_username: str = "admin"
    admin_password: str = ""
    temperature: float = 0.0
    timeout: int = 90
    tesseract_cmd: str = ""
    recovery_on_startup: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context):
        self.data_path = Path(self.data_path).expanduser().resolve()
        defaults = {
            "uploads_path": self.data_path / "uploads",
            "extracted_path": self.data_path / "extracted",
            "chroma_path": self.data_path / "chroma_db",
            "metadata_path": self.data_path / "metadata",
            "logs_path": self.data_path / "logs",
            "jobs_path": self.data_path / "jobs",
            "sqlite_path": self.data_path / "metadata" / "documents.sqlite3",
        }
        for key, default in defaults.items():
            value = getattr(self, key)
            setattr(self, key, Path(value).expanduser().resolve() if value else default.resolve())

settings = Settings()
