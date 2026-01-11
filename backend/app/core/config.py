import os
import logging
import re
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # API
    SORA_API_KEY: str = Field(..., env="SORA_API_KEY")
    SORA_BASE_URL: str = Field("https://api.sora.hk/v1", env="SORA_BASE_URL")
    AUTH_TOKEN: Optional[str] = Field(None, env="AUTH_TOKEN")
    CORS_ALLOW_ORIGINS: Optional[str] = Field("*", env="CORS_ALLOW_ORIGINS")
    
    # Execution
    MAX_CONCURRENT_TASKS: int = Field(20, env="MAX_CONCURRENT_TASKS")
    GEN_COUNT_PER_SEGMENT: int = Field(2, env="GEN_COUNT_PER_SEGMENT")
    MAX_POLL_TIME: int = Field(2100, env="MAX_POLL_TIME")
    POLL_INITIAL_WAIT_SECONDS: int = Field(20, env="POLL_INITIAL_WAIT_SECONDS")
    POLL_INTERVAL_SECONDS: int = Field(10, env="POLL_INTERVAL_SECONDS")
    API_REQUEST_TIMEOUT_SECONDS: int = Field(30, env="API_REQUEST_TIMEOUT_SECONDS")
    DOWNLOAD_TIMEOUT_SECONDS: int = Field(300, env="DOWNLOAD_TIMEOUT_SECONDS")
    CONCURRENCY_MIN_TASKS: int = Field(5, env="CONCURRENCY_MIN_TASKS")
    CONCURRENCY_ERROR_THRESHOLD: int = Field(2, env="CONCURRENCY_ERROR_THRESHOLD")
    CONCURRENCY_COOLDOWN_SECONDS: int = Field(600, env="CONCURRENCY_COOLDOWN_SECONDS")
    CONCURRENCY_RECOVERY_RATE_SECONDS: int = Field(60, env="CONCURRENCY_RECOVERY_RATE_SECONDS")

    # Failover error classification overrides
    FAILOVER_RETRYABLE_TOKENS: Optional[str] = Field(None, env="FAILOVER_RETRYABLE_TOKENS")
    FAILOVER_NON_RETRYABLE_TOKENS: Optional[str] = Field(None, env="FAILOVER_NON_RETRYABLE_TOKENS")
    
    # Proxy
    HTTP_PROXY: Optional[str] = Field(None, env="HTTP_PROXY")
    HTTPS_PROXY: Optional[str] = Field(None, env="HTTPS_PROXY")
    
    # Paths
    # Adjusted for backend/app/core/config.py structure (4 levels deep from root)
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.parent
    DEFAULT_INPUT_DIR: Path = PROJECT_ROOT / "input"
    DEFAULT_OUTPUT_DIR: Path = PROJECT_ROOT / "output"

    # Tencent COS (Optional)
    COS_SECRET_ID: Optional[str] = Field(None, env="COS_SECRET_ID")
    COS_SECRET_KEY: Optional[str] = Field(None, env="COS_SECRET_KEY")
    COS_REGION: Optional[str] = Field(None, env="COS_REGION")
    COS_BUCKET: Optional[str] = Field(None, env="COS_BUCKET")
    COS_CUSTOM_DOMAIN: Optional[str] = Field(None, env="COS_CUSTOM_DOMAIN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

class SensitiveFilter(logging.Filter):
    """
    Filters out sensitive information like API Keys from logs.
    """
    def __init__(self, patterns=None):
        super().__init__()
        self.patterns = patterns or []

    def filter(self, record):
        msg = record.getMessage()
        # Mask the configured API Key
        if settings.SORA_API_KEY in msg:
            msg = msg.replace(settings.SORA_API_KEY, "sk-******")
        
        # Mask any other potential Bearer tokens using Regex
        msg = re.sub(r'Bearer\s+sk-[a-zA-Z0-9]+', 'Bearer sk-******', msg)
        
        record.msg = msg
        record.args = () # Clear args to prevent reformation
        return True

def setup_logging(verbose: bool = False):
    """Configures logging for the application with security filtering."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create Handler
    file_handler = logging.FileHandler(settings.PROJECT_ROOT / "app.log", encoding='utf-8')
    console_handler = logging.StreamHandler() # Standard stream for fallback
    
    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    file_handler.setFormatter(formatter)
    
    # Add Security Filter
    sensitive_filter = SensitiveFilter()
    file_handler.addFilter(sensitive_filter)
    # Note: RichHandler in main.py also needs this filter if we want to be super safe, 
    # but Rich handles formatting differently. We apply it at the logger level mainly.
    
    # Root Logger Config
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(file_handler)
    
    # Apply filter to root logger to catch everything
    root_logger.addFilter(sensitive_filter)
