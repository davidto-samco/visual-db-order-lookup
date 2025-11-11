"""Configuration management using environment variables."""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from .env file."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Load configuration from .env file.

        Args:
            env_file: Path to .env file. If None, searches for .env in current directory.
        """
        if env_file:
            env_path = Path(env_file)
        else:
            # Search for .env in current directory and parent directories
            current_dir = Path.cwd()
            env_path = current_dir / ".env"

            # If not found in current directory, check parent directories
            if not env_path.exists():
                for parent in current_dir.parents:
                    potential_env = parent / ".env"
                    if potential_env.exists():
                        env_path = potential_env
                        break

        if env_path.exists():
            load_dotenv(env_path)
        else:
            raise FileNotFoundError(
                f"Configuration file .env not found. Please create one based on .env.example"
            )

    @property
    def connection_string(self) -> str:
        """Get database connection string from environment."""
        conn_str = os.getenv("MSSQL_CONNECTION_STRING")
        if not conn_str:
            raise ValueError(
                "MSSQL_CONNECTION_STRING not found in environment. "
                "Please check your .env file."
            )
        return conn_str

    @property
    def app_name(self) -> str:
        """Get application name."""
        return os.getenv("APP_NAME", "Visual Order Lookup")

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv("LOG_LEVEL", "INFO")

    def setup_logging(self) -> None:
        """Configure application logging."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)

        # Configure logging format
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create logger for connection errors only (no customer data)
        logger = logging.getLogger("visual_order_lookup")
        logger.setLevel(log_level)

        # Add file handler for errors
        log_file = Path.cwd() / "visual_order_lookup.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
