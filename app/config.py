from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    master_key: str
    gemini_api_keys: str  # comma-separated
    mistral_api_key: str = ""
    default_model: str = "gemini-2.5-flash"
    rate_limit_per_minute: int = 60
    db_path: str = "data/gateway.db"

    @property
    def gemini_keys_list(self) -> list[str]:
        return [k.strip() for k in self.gemini_api_keys.split(",") if k.strip()]

    model_config = {"env_file": ".env"}


settings = Settings()
