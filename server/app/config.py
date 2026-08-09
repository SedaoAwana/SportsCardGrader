from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_env: str = "production"  # or "sandbox"
    anthropic_default_model: str = "claude-sonnet-5"
    openai_default_model: str = "gpt-5.1"

    model_config = {"env_file": ".env"}

    @property
    def ebay_configured(self) -> bool:
        return bool(self.ebay_client_id and self.ebay_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
