from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    cron_secret: str = ""
    missed_dose_grace_minutes: int = 60
    fcm_enabled: bool = False
    firebase_credentials_path: str = ""
    # Used on Vercel, where the key file does not exist: the full JSON text of the key
    firebase_credentials_json: str = ""
    # Set this to true on Vercel (serverless): do not keep database connections open
    db_null_pool: bool = False

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()