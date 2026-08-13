from functools import lru_cache

from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@lru_cache()
def get_settings() -> Settings:
    return Settings()