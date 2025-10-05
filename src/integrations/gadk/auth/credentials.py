"""
GADK Authentication and Credentials Management

This module provides secure authentication and credential management for Google Cloud services
used in the GADK integration including Vertex AI, Discovery Engine, and Dialogflow.

Features:
- Service account authentication with JSON key files
- Environment-based credential configuration
- Credential validation and health checks
- Secure credential storage and access
- Token refresh and session management
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from google.auth import default
    from google.auth.exceptions import DefaultCredentialsError, RefreshError
    from google.oauth2 import service_account
    import google.auth.transport.requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    # Fallback types for when Google Auth is not available
    class DefaultCredentialsError(Exception):
        pass
    
    class RefreshError(Exception):
        pass


logger = logging.getLogger(__name__)


@dataclass
class CredentialInfo:
    """Information about loaded credentials."""
    project_id: str
    service_account_email: Optional[str] = None
    key_id: Optional[str] = None
    credential_type: str = "default"
    is_valid: bool = False
    expires_at: Optional[str] = None


class GADKCredentialManager:
    """
    Manager for Google Cloud credentials used in GADK integration.
    
    Provides secure credential loading, validation, and management for:
    - Service account JSON key files
    - Default application credentials
    - Environment-based authentication
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the credential manager.
        
        Args:
            credentials_path: Optional path to service account JSON key file
        """
        self.credentials_path = credentials_path
        self._credentials = None
        self._project_id = None
        self._credential_info = None
        
    def load_credentials(self, force_reload: bool = False) -> bool:
        """
        Load Google Cloud credentials from various sources.
        
        Args:
            force_reload: Whether to force reload credentials even if already loaded
            
        Returns:
            bool: True if credentials loaded successfully, False otherwise
        """
        if not GOOGLE_AUTH_AVAILABLE:
            logger.error("Google Auth libraries not available. Install with: poetry install")
            return False
            
        if self._credentials and not force_reload:
            logger.info("Credentials already loaded")
            return True
            
        try:
            # Try loading from specified credentials path first
            if self.credentials_path and self._load_service_account_credentials():
                return True
                
            # Try loading from environment variable
            env_creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if env_creds_path and self._load_service_account_credentials(env_creds_path):
                return True
                
            # Fall back to default application credentials
            if self._load_default_credentials():
                return True
                
            logger.error("Failed to load credentials from any source")
            return False
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return False
    
    def validate_credentials(self) -> bool:
        """
        Validate that loaded credentials are working and have proper permissions.
        
        Returns:
            bool: True if credentials are valid and working, False otherwise
        """
        if not self._credentials:
            logger.error("No credentials loaded to validate")
            return False
            
        try:
            # Refresh credentials to ensure they're valid
            request = google.auth.transport.requests.Request()
            self._credentials.refresh(request)
            
            # Update credential info
            if self._credential_info:
                self._credential_info.is_valid = True
                
            logger.info("Credentials validated successfully")
            return True
            
        except RefreshError as e:
            logger.error(f"Credential validation failed: {e}")
            if self._credential_info:
                self._credential_info.is_valid = False
            return False
        except Exception as e:
            logger.error(f"Error validating credentials: {e}")
            return False
    
    def get_credentials(self):
        """
        Get the loaded Google Cloud credentials.
        
        Returns:
            google.auth.credentials.Credentials: The loaded credentials or None
        """
        return self._credentials
    
    def get_project_id(self) -> Optional[str]:
        """
        Get the project ID associated with the loaded credentials.
        
        Returns:
            str: The project ID or None if not available
        """
        return self._project_id
    
    def get_credential_info(self) -> Optional[CredentialInfo]:
        """
        Get information about the loaded credentials.
        
        Returns:
            CredentialInfo: Information about the credentials or None
        """
        return self._credential_info
    
    def has_valid_credentials(self) -> bool:
        """
        Check if valid credentials are loaded and ready to use.
        
        Returns:
            bool: True if valid credentials are available, False otherwise
        """
        return (self._credentials is not None and 
                self._credential_info is not None and 
                self._credential_info.is_valid)
    
    def refresh_credentials(self) -> bool:
        """
        Refresh the loaded credentials.
        
        Returns:
            bool: True if credentials refreshed successfully, False otherwise
        """
        if not self._credentials:
            logger.error("No credentials to refresh")
            return False
            
        try:
            request = google.auth.transport.requests.Request()
            self._credentials.refresh(request)
            logger.info("Credentials refreshed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh credentials: {e}")
            return False
    
    def clear_credentials(self) -> None:
        """Clear all loaded credentials and credential information."""
        self._credentials = None
        self._project_id = None
        self._credential_info = None
        logger.info("Credentials cleared")
    
    # Private methods for credential loading
    
    def _load_service_account_credentials(self, path: Optional[str] = None) -> bool:
        """Load credentials from a service account JSON key file."""
        if not GOOGLE_AUTH_AVAILABLE:
            return False
            
        creds_path = path or self.credentials_path
        if not creds_path:
            return False
            
        try:
            # Verify file exists and is readable
            if not Path(creds_path).is_file():
                logger.error(f"Credentials file not found: {creds_path}")
                return False
                
            # Load service account credentials
            self._credentials = service_account.Credentials.from_service_account_file(creds_path)
            
            # Extract project ID from credentials or file
            if hasattr(self._credentials, 'project_id'):
                self._project_id = self._credentials.project_id
            else:
                # Try to extract from the JSON file
                self._project_id = self._extract_project_id_from_file(creds_path)
            
            # Create credential info
            service_account_info = self._extract_service_account_info(creds_path)
            self._credential_info = CredentialInfo(
                project_id=self._project_id or "unknown",
                service_account_email=service_account_info.get('client_email'),
                key_id=service_account_info.get('private_key_id'),
                credential_type="service_account",
                is_valid=False  # Will be validated separately
            )
            
            logger.info(f"Service account credentials loaded from: {creds_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load service account credentials from {creds_path}: {e}")
            return False
    
    def _load_default_credentials(self) -> bool:
        """Load default application credentials."""
        if not GOOGLE_AUTH_AVAILABLE:
            return False
            
        try:
            self._credentials, self._project_id = default()
            
            # Create credential info
            self._credential_info = CredentialInfo(
                project_id=self._project_id or "unknown",
                credential_type="default",
                is_valid=False  # Will be validated separately
            )
            
            logger.info("Default application credentials loaded")
            return True
            
        except DefaultCredentialsError as e:
            logger.error(f"Failed to load default credentials: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading default credentials: {e}")
            return False
    
    def _extract_project_id_from_file(self, creds_path: str) -> Optional[str]:
        """Extract project ID from service account JSON file."""
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
                return creds_data.get('project_id')
        except Exception as e:
            logger.error(f"Failed to extract project ID from {creds_path}: {e}")
            return None
    
    def _extract_service_account_info(self, creds_path: str) -> Dict[str, Any]:
        """Extract service account information from JSON file."""
        try:
            with open(creds_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to extract service account info from {creds_path}: {e}")
            return {}


def get_credentials_from_environment() -> Tuple[Optional[Any], Optional[str]]:
    """
    Get Google Cloud credentials from environment variables.
    
    Returns:
        Tuple of (credentials, project_id) or (None, None) if not available
    """
    if not GOOGLE_AUTH_AVAILABLE:
        logger.error("Google Auth libraries not available")
        return None, None
        
    credential_manager = GADKCredentialManager()
    
    if credential_manager.load_credentials():
        if credential_manager.validate_credentials():
            return credential_manager.get_credentials(), credential_manager.get_project_id()
    
    return None, None


def validate_credentials_file(credentials_path: str) -> bool:
    """
    Validate that a credentials file is properly formatted and accessible.
    
    Args:
        credentials_path: Path to the credentials file
        
    Returns:
        bool: True if file is valid, False otherwise
    """
    try:
        # Check if file exists
        if not Path(credentials_path).is_file():
            logger.error(f"Credentials file not found: {credentials_path}")
            return False
            
        # Try to parse as JSON
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
            
        # Check for required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in creds_data]
        
        if missing_fields:
            logger.error(f"Credentials file missing required fields: {missing_fields}")
            return False
            
        # Check if it's a service account
        if creds_data.get('type') != 'service_account':
            logger.error("Credentials file is not a service account key")
            return False
            
        logger.info(f"Credentials file validated: {credentials_path}")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Credentials file is not valid JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating credentials file: {e}")
        return False


def create_credential_manager_from_config(config: Dict[str, Any]) -> GADKCredentialManager:
    """
    Create a credential manager from configuration.
    
    Args:
        config: Configuration dictionary with credential settings
        
    Returns:
        GADKCredentialManager: Initialized credential manager
    """
    credentials_path = config.get('credentials_path', os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    return GADKCredentialManager(credentials_path=credentials_path)


def ensure_credentials_available() -> bool:
    """
    Ensure that Google Cloud credentials are available and valid.
    
    Returns:
        bool: True if valid credentials are available, False otherwise
    """
    credential_manager = GADKCredentialManager()
    
    if not credential_manager.load_credentials():
        logger.error("Failed to load Google Cloud credentials")
        return False
        
    if not credential_manager.validate_credentials():
        logger.error("Google Cloud credentials are not valid")
        return False
        
    logger.info("Google Cloud credentials are available and valid")
    return True