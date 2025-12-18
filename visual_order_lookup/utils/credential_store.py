"""Secure credential storage using Windows Credential Manager."""

import logging
import json
from typing import Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

logger = logging.getLogger(__name__)


class CredentialStore:
    """Manage secure storage of database credentials."""

    SERVICE_NAME = "VisualOrderLookup"
    USERNAME_KEY = "database_credentials"

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if credential storage is available on this system.

        Returns:
            True if credential storage is available
        """
        return KEYRING_AVAILABLE

    @classmethod
    def save_credentials(cls, server: str, database: str, username: str, password: str) -> bool:
        """
        Save database credentials securely.

        Args:
            server: Database server address
            database: Database name
            username: Database username
            password: Database password

        Returns:
            True if credentials were saved successfully, False otherwise
        """
        if not cls.is_available():
            logger.warning("Credential storage not available - keyring package not installed")
            return False

        try:
            credentials = {
                'server': server,
                'database': database,
                'username': username
            }

            # Store credentials JSON in keyring
            keyring.set_password(
                cls.SERVICE_NAME,
                cls.USERNAME_KEY,
                json.dumps(credentials)
            )

            # Store password separately
            keyring.set_password(
                cls.SERVICE_NAME,
                f"{cls.USERNAME_KEY}_password",
                password
            )

            logger.info("Credentials saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False

    @classmethod
    def load_credentials(cls) -> Optional[dict]:
        """
        Load saved database credentials.

        Returns:
            Dictionary with 'server', 'database', 'username', 'password' or None
        """
        if not cls.is_available():
            return None

        try:
            # Load credentials JSON
            credentials_json = keyring.get_password(cls.SERVICE_NAME, cls.USERNAME_KEY)
            if not credentials_json:
                return None

            credentials = json.loads(credentials_json)

            # Load password
            password = keyring.get_password(cls.SERVICE_NAME, f"{cls.USERNAME_KEY}_password")
            if not password:
                return None

            credentials['password'] = password
            logger.info("Credentials loaded successfully")
            return credentials

        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None

    @classmethod
    def delete_credentials(cls) -> bool:
        """
        Delete saved credentials.

        Returns:
            True if credentials were deleted successfully
        """
        if not cls.is_available():
            return False

        try:
            keyring.delete_password(cls.SERVICE_NAME, cls.USERNAME_KEY)
            keyring.delete_password(cls.SERVICE_NAME, f"{cls.USERNAME_KEY}_password")
            logger.info("Credentials deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
