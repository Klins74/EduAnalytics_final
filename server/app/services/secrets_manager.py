"""
Secrets Management Service with multiple backend support.

Supports Docker Secrets, HashiCorp Vault, AWS Secrets Manager, and local fallback.
"""

import logging
import os
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiofiles
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecretBackend(Enum):
    """Supported secret management backends."""
    DOCKER_SECRETS = "docker_secrets"
    VAULT = "vault"
    AWS_SECRETS = "aws_secrets"
    LOCAL_FILE = "local_file"
    ENVIRONMENT = "environment"


@dataclass
class SecretInfo:
    """Information about a secret."""
    key: str
    value: str
    backend: SecretBackend
    encrypted: bool = False
    metadata: Optional[Dict[str, Any]] = None


class LocalEncryption:
    """Local encryption for storing secrets securely."""
    
    def __init__(self, password: Optional[str] = None):
        self.password = password or os.environ.get('SECRET_ENCRYPTION_KEY', 'default-key')
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet encryption instance."""
        if self._fernet is None:
            # Derive key from password
            password_bytes = self.password.encode()
            salt = b'eduanalytics_salt'  # In production, use random salt stored securely
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self._get_fernet().encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        return self._get_fernet().decrypt(encrypted_data.encode()).decode()


class DockerSecretsProvider:
    """Provider for Docker Secrets."""
    
    def __init__(self, secrets_path: str = "/run/secrets"):
        self.secrets_path = Path(secrets_path)
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Docker secrets."""
        try:
            secret_file = self.secrets_path / key
            if secret_file.exists():
                async with aiofiles.open(secret_file, 'r') as f:
                    content = await f.read()
                    return content.strip()
            return None
        except Exception as e:
            logger.error(f"Error reading Docker secret {key}: {e}")
            return None
    
    async def list_secrets(self) -> Dict[str, str]:
        """List all available Docker secrets."""
        secrets = {}
        try:
            if self.secrets_path.exists():
                for secret_file in self.secrets_path.iterdir():
                    if secret_file.is_file():
                        async with aiofiles.open(secret_file, 'r') as f:
                            content = await f.read()
                            secrets[secret_file.name] = content.strip()
        except Exception as e:
            logger.error(f"Error listing Docker secrets: {e}")
        return secrets


class VaultProvider:
    """Provider for HashiCorp Vault."""
    
    def __init__(self, vault_url: str, vault_token: str, vault_path: str = "secret"):
        self.vault_url = vault_url.rstrip('/')
        self.vault_token = vault_token
        self.vault_path = vault_path
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault."""
        try:
            import aiohttp
            
            headers = {'X-Vault-Token': self.vault_token}
            url = f"{self.vault_url}/v1/{self.vault_path}/data/{key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('data', {}).get('value')
                    else:
                        logger.warning(f"Vault returned status {response.status} for secret {key}")
                        return None
        except Exception as e:
            logger.error(f"Error getting secret from Vault: {e}")
            return None
    
    async def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Set secret in Vault."""
        try:
            import aiohttp
            
            headers = {
                'X-Vault-Token': self.vault_token,
                'Content-Type': 'application/json'
            }
            url = f"{self.vault_url}/v1/{self.vault_path}/data/{key}"
            
            payload = {
                'data': {
                    'value': value,
                    'metadata': metadata or {}
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    return response.status in [200, 204]
        except Exception as e:
            logger.error(f"Error setting secret in Vault: {e}")
            return False


class LocalFileProvider:
    """Provider for local encrypted file storage."""
    
    def __init__(self, secrets_file: str = "secrets.json"):
        self.secrets_file = Path(secrets_file)
        self.encryption = LocalEncryption()
        self._secrets_cache = None
    
    async def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets from file."""
        if self._secrets_cache is not None:
            return self._secrets_cache
        
        try:
            if self.secrets_file.exists():
                async with aiofiles.open(self.secrets_file, 'r') as f:
                    content = await f.read()
                    if content.strip():
                        # Try to decrypt if the content looks encrypted
                        try:
                            decrypted = self.encryption.decrypt(content)
                            self._secrets_cache = json.loads(decrypted)
                        except:
                            # If decryption fails, assume it's plain JSON
                            self._secrets_cache = json.loads(content)
                    else:
                        self._secrets_cache = {}
            else:
                self._secrets_cache = {}
        except Exception as e:
            logger.error(f"Error loading secrets file: {e}")
            self._secrets_cache = {}
        
        return self._secrets_cache
    
    async def _save_secrets(self, secrets: Dict[str, Any]) -> bool:
        """Save secrets to file."""
        try:
            # Encrypt the JSON data
            json_data = json.dumps(secrets, indent=2)
            encrypted_data = self.encryption.encrypt(json_data)
            
            async with aiofiles.open(self.secrets_file, 'w') as f:
                await f.write(encrypted_data)
            
            self._secrets_cache = secrets
            return True
        except Exception as e:
            logger.error(f"Error saving secrets file: {e}")
            return False
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from local file."""
        secrets = await self._load_secrets()
        return secrets.get(key)
    
    async def set_secret(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Set secret in local file."""
        secrets = await self._load_secrets()
        secrets[key] = {
            'value': value,
            'metadata': metadata or {},
            'created_at': str(asyncio.get_event_loop().time())
        }
        return await self._save_secrets(secrets)
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from local file."""
        secrets = await self._load_secrets()
        if key in secrets:
            del secrets[key]
            return await self._save_secrets(secrets)
        return False


class SecretsManager:
    """Main secrets manager with multiple backend support."""
    
    def __init__(self):
        self.backends = self._initialize_backends()
        self.default_backend = self._get_default_backend()
    
    def _initialize_backends(self) -> Dict[SecretBackend, Any]:
        """Initialize available secret backends."""
        backends = {}
        
        # Environment variables (always available)
        backends[SecretBackend.ENVIRONMENT] = None
        
        # Docker Secrets
        docker_secrets_path = os.environ.get('DOCKER_SECRETS_PATH', '/run/secrets')
        if Path(docker_secrets_path).exists():
            backends[SecretBackend.DOCKER_SECRETS] = DockerSecretsProvider(docker_secrets_path)
            logger.info("Docker Secrets backend initialized")
        
        # HashiCorp Vault
        vault_url = os.environ.get('VAULT_URL')
        vault_token = os.environ.get('VAULT_TOKEN')
        if vault_url and vault_token:
            vault_path = os.environ.get('VAULT_SECRET_PATH', 'secret')
            backends[SecretBackend.VAULT] = VaultProvider(vault_url, vault_token, vault_path)
            logger.info("Vault backend initialized")
        
        # Local file storage (always available as fallback)
        secrets_file = os.environ.get('SECRETS_FILE', 'server/secrets.enc')
        backends[SecretBackend.LOCAL_FILE] = LocalFileProvider(secrets_file)
        logger.info("Local file backend initialized")
        
        return backends
    
    def _get_default_backend(self) -> SecretBackend:
        """Determine the default backend to use."""
        preferred_order = [
            SecretBackend.DOCKER_SECRETS,
            SecretBackend.VAULT,
            SecretBackend.LOCAL_FILE,
            SecretBackend.ENVIRONMENT
        ]
        
        for backend in preferred_order:
            if backend in self.backends:
                logger.info(f"Using {backend.value} as default secrets backend")
                return backend
        
        return SecretBackend.ENVIRONMENT
    
    async def get_secret(
        self, 
        key: str, 
        backend: Optional[SecretBackend] = None,
        fallback_to_env: bool = True
    ) -> Optional[str]:
        """
        Get a secret from the specified backend or default backend.
        
        Args:
            key: Secret key
            backend: Specific backend to use
            fallback_to_env: Whether to fallback to environment variables
            
        Returns:
            Secret value or None if not found
        """
        backend = backend or self.default_backend
        
        try:
            # Try the specified backend
            if backend == SecretBackend.ENVIRONMENT:
                return os.environ.get(key)
            elif backend in self.backends:
                provider = self.backends[backend]
                if provider:
                    value = await provider.get_secret(key)
                    if value:
                        return value
            
            # Fallback to environment variables if enabled
            if fallback_to_env and backend != SecretBackend.ENVIRONMENT:
                env_value = os.environ.get(key)
                if env_value:
                    logger.debug(f"Found secret {key} in environment variables as fallback")
                    return env_value
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting secret {key} from {backend.value}: {e}")
            return None
    
    async def set_secret(
        self, 
        key: str, 
        value: str, 
        backend: Optional[SecretBackend] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set a secret in the specified backend.
        
        Args:
            key: Secret key
            value: Secret value
            backend: Backend to store in
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        backend = backend or self.default_backend
        
        try:
            if backend == SecretBackend.ENVIRONMENT:
                os.environ[key] = value
                return True
            elif backend in self.backends:
                provider = self.backends[backend]
                if provider and hasattr(provider, 'set_secret'):
                    return await provider.set_secret(key, value, metadata)
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting secret {key} in {backend.value}: {e}")
            return False
    
    async def delete_secret(self, key: str, backend: Optional[SecretBackend] = None) -> bool:
        """Delete a secret from the specified backend."""
        backend = backend or self.default_backend
        
        try:
            if backend == SecretBackend.ENVIRONMENT:
                if key in os.environ:
                    del os.environ[key]
                    return True
                return False
            elif backend in self.backends:
                provider = self.backends[backend]
                if provider and hasattr(provider, 'delete_secret'):
                    return await provider.delete_secret(key)
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting secret {key} from {backend.value}: {e}")
            return False
    
    async def list_secrets(self, backend: Optional[SecretBackend] = None) -> Dict[str, SecretInfo]:
        """List all secrets from the specified backend."""
        backend = backend or self.default_backend
        secrets = {}
        
        try:
            if backend == SecretBackend.ENVIRONMENT:
                # Return environment variables that look like secrets
                secret_prefixes = ['SECRET_', 'API_KEY_', 'TOKEN_', 'PASSWORD_']
                for key, value in os.environ.items():
                    if any(key.startswith(prefix) for prefix in secret_prefixes):
                        secrets[key] = SecretInfo(
                            key=key,
                            value="***masked***",  # Don't expose actual values
                            backend=backend,
                            metadata={'source': 'environment'}
                        )
            elif backend in self.backends:
                provider = self.backends[backend]
                if provider and hasattr(provider, 'list_secrets'):
                    raw_secrets = await provider.list_secrets()
                    for key, value in raw_secrets.items():
                        secrets[key] = SecretInfo(
                            key=key,
                            value="***masked***",  # Don't expose actual values
                            backend=backend
                        )
        except Exception as e:
            logger.error(f"Error listing secrets from {backend.value}: {e}")
        
        return secrets
    
    async def rotate_secret(self, key: str, new_value: str, backend: Optional[SecretBackend] = None) -> bool:
        """Rotate a secret by updating its value."""
        success = await self.set_secret(key, new_value, backend)
        if success:
            logger.info(f"Successfully rotated secret {key}")
        return success
    
    async def get_database_url(self) -> str:
        """Get database URL from secrets or environment."""
        # Try to get from secrets first
        db_url = await self.get_secret('DATABASE_URL')
        if db_url:
            return db_url
        
        # Construct from individual components
        db_host = await self.get_secret('DB_HOST') or 'localhost'
        db_port = await self.get_secret('DB_PORT') or '5432'
        db_name = await self.get_secret('DB_NAME') or 'eduanalytics'
        db_user = await self.get_secret('DB_USER') or 'postgres'
        db_password = await self.get_secret('DB_PASSWORD') or 'password'
        
        return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    async def get_redis_url(self) -> str:
        """Get Redis URL from secrets or environment."""
        redis_url = await self.get_secret('REDIS_URL')
        if redis_url:
            return redis_url
        
        # Construct from individual components
        redis_host = await self.get_secret('REDIS_HOST') or 'localhost'
        redis_port = await self.get_secret('REDIS_PORT') or '6379'
        redis_password = await self.get_secret('REDIS_PASSWORD')
        
        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        else:
            return f"redis://{redis_host}:{redis_port}/0"
    
    async def get_secret_config(self) -> Dict[str, str]:
        """Get all application secrets as a configuration dictionary."""
        config = {}
        
        # Core secrets
        secret_keys = [
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_URL',
            'CANVAS_API_KEY',
            'CANVAS_API_SECRET',
            'JWT_SECRET_KEY',
            'ENCRYPTION_KEY',
            'SENTRY_DSN',
            'EMAIL_HOST_PASSWORD',
            'TWILIO_AUTH_TOKEN',
            'AWS_SECRET_ACCESS_KEY',
            'TELEGRAM_BOT_TOKEN',
            'OPENAI_API_KEY',
            'GOOGLE_API_KEY'
        ]
        
        for key in secret_keys:
            value = await self.get_secret(key)
            if value:
                config[key] = value
        
        return config


# Global secrets manager instance
secrets_manager = SecretsManager()
