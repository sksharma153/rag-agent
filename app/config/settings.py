from functools import lru_cache

from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    #GCP
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "rag")
    BIGQUERY_DOCUMENTS_TABLE = os.getenv("BIGQUERY_DOCUMENTS_TABLE", "documents")
    BIGQUERY_CHUNK_TABLE = os.getenv("BIGQUERY_CHUNK_TABLE", "chunks")

@lru_cache()
def get_settings() -> Settings:
    return Settings()