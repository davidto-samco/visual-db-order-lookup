"""Configuration management using environment variables."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Application configuration loaded from .env file or manual credentials."""

    def __init__(self, env_file: Optional[str] = None, manual_credentials: Optional[dict] = None):
        """
        Load configuration from .env file or manual credentials.

        Args:
            env_file: Path to .env file. If None, searches for .env in current directory.
            manual_credentials: Dictionary with 'server', 'database', 'username', 'password'.
                              If provided, takes precedence over .env file.
        """
        self._manual_connection_string = None

        if manual_credentials:
            # Use manual credentials to build connection string
            self._manual_connection_string = self._build_connection_string(
                manual_credentials['server'],
                manual_credentials['database'],
                manual_credentials['username'],
                manual_credentials['password']
            )
        else:
            # Try to load from .env file
            if env_file:
                env_path = Path(env_file)
            else:
                # Get the directory where the app is running from
                if getattr(sys, 'frozen', False):
                    # Running as compiled executable - only check exe directory
                    app_dir = Path(sys.executable).parent
                else:
                    # Running as script - check current directory and parents
                    app_dir = Path.cwd()

                env_path = app_dir / ".env"

                # If running as script and not found, check parent directories
                if not env_path.exists() and not getattr(sys, 'frozen', False):
                    for parent in app_dir.parents:
                        potential_env = parent / ".env"
                        if potential_env.exists():
                            env_path = potential_env
                            break

            if env_path.exists():
                load_dotenv(env_path)
            else:
                # No .env file and no manual credentials
                raise FileNotFoundError(
                    f"Configuration file .env not found. Please create one based on .env.example"
                )

    @staticmethod
    def _build_connection_string(server: str, database: str, username: str, password: str) -> str:
        """
        Build ODBC connection string from components.

        Args:
            server: Server address (e.g., "10.10.10.142,1433")
            database: Database name
            username: Database username
            password: Database password

        Returns:
            Complete ODBC connection string
        """
        return (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={server};"
            f"Database={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )

    @property
    def connection_string(self) -> str:
        """Get database connection string from manual credentials or environment."""
        # Use manual connection string if available
        if self._manual_connection_string:
            return self._manual_connection_string

        # Otherwise get from environment (.env file)
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


def set_config(config: Config) -> None:
    """
    Set the global config instance.

    Args:
        config: Config instance to set as global
    """
    global _config
    _config = config


def has_env_file() -> bool:
    """
    Check if .env file exists.

    When running as executable: only checks in exe directory
    When running as script: checks current directory and parent directories

    Returns:
        True if .env file exists, False otherwise
    """
    # Get the directory where the app is running from
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - only check exe directory
        app_dir = Path(sys.executable).parent
        env_path = app_dir / ".env"
        return env_path.exists()
    else:
        # Running as script - check current directory and parents
        current_dir = Path.cwd()
        env_path = current_dir / ".env"

        if env_path.exists():
            return True

        # Check parent directories
        for parent in current_dir.parents:
            potential_env = parent / ".env"
            if potential_env.exists():
                return True

        return False
