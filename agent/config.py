from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
TAILORED_DIR = OUTPUT_DIR / "tailored_resumes"
APPLICATIONS_DIR = OUTPUT_DIR / "applications"
DB_PATH = ROOT_DIR / "jobs.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3-32b"
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "in"
    min_fit_score: int = 25
    max_jobs_per_search: int = 30


settings = Settings()

for path in (DATA_DIR, OUTPUT_DIR, TAILORED_DIR, APPLICATIONS_DIR):
    path.mkdir(parents=True, exist_ok=True)