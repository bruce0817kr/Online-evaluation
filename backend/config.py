import os

class Settings:
    PROJECT_NAME: str = "Online Evaluation System"
    PROJECT_VERSION: str = "1.0.0"

    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_in_env_var")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "online_evaluation_db")

    # Environment settings
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development") # development, staging, production

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"] # Adjust in production

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # Email settings (example, adjust as needed)
    # MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")
    # MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    # MAIL_FROM: str = os.getenv("MAIL_FROM")
    # MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))
    # MAIL_SERVER: str = os.getenv("MAIL_SERVER")
    # MAIL_TLS: bool = True
    # MAIL_SSL: bool = False

    # Test user credentials (for initial setup or testing)
    # These should ideally be managed securely, not hardcoded
    ADMIN_LOGIN_ID: str = "admin"
    ADMIN_PASSWORD: str = "adminpass" # Store hashed passwords in production

    # File upload settings
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 10 # Max file size in MB

    # API Prefixes
    API_V1_STR: str = "/api/v1"

settings = Settings()
