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
    
    # Execution
    MAX_CONCURRENT_TASKS: int = Field(20, env="MAX_CONCURRENT_TASKS")
    GEN_COUNT_PER_SEGMENT: int = Field(2, env="GEN_COUNT_PER_SEGMENT")
    
    # Proxy
    HTTP_PROXY: Optional[str] = Field(None, env="HTTP_PROXY")
    HTTPS_PROXY: Optional[str] = Field(None, env="HTTPS_PROXY")
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DEFAULT_INPUT_DIR: Path = PROJECT_ROOT / "input"
    DEFAULT_OUTPUT_DIR: Path = PROJECT_ROOT / "output"

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