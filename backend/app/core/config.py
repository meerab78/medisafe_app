from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080

    # Secret used by cron-job.org to call the internal job endpoints
    cron_secret: str = ""
    # A pending dose becomes "missed" this many minutes after its time
    missed_dose_grace_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()