from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/workflowsync"
    
    # Security / Auth settings
    SECRET_KEY: str = "your-super-secret-key-that-should-be-overridden-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024 # 5 MB default
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
