"""
Security configuration with secrets management integration.

Replaces hardcoded secrets with secure retrieval from various backends.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from functools import lru_cache

from app.services.secrets_manager import secrets_manager
from app.core.config import Settings

logger = logging.getLogger(__name__)


class SecureSettings(Settings):
    """Enhanced settings class with secrets management."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._secrets_loaded = False
        self._secret_cache = {}
    
    async def load_secrets(self):
        """Load secrets from the secrets manager."""
        if self._secrets_loaded:
            return
        
        try:
            # Get all application secrets
            secret_config = await secrets_manager.get_secret_config()
            
            # Update configuration with secrets
            for key, value in secret_config.items():
                if hasattr(self, key.lower()):
                    setattr(self, key.lower(), value)
                self._secret_cache[key] = value
            
            # Handle special cases
            await self._load_database_config()
            await self._load_redis_config()
            await self._load_external_api_config()
            
            self._secrets_loaded = True
            logger.info("Successfully loaded secrets from secrets manager")
            
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            # Don't fail startup, continue with environment variables
    
    async def _load_database_config(self):
        """Load database configuration from secrets."""
        try:
            db_url = await secrets_manager.get_database_url()
            if db_url:
                self.database_url = db_url
                logger.debug("Database URL loaded from secrets")
        except Exception as e:
            logger.error(f"Error loading database config: {e}")
    
    async def _load_redis_config(self):
        """Load Redis configuration from secrets."""
        try:
            redis_url = await secrets_manager.get_redis_url()
            if redis_url:
                self.redis_url = redis_url
                logger.debug("Redis URL loaded from secrets")
        except Exception as e:
            logger.error(f"Error loading Redis config: {e}")
    
    async def _load_external_api_config(self):
        """Load external API configurations from secrets."""
        try:
            # Canvas API
            canvas_key = await secrets_manager.get_secret('CANVAS_API_KEY')
            canvas_secret = await secrets_manager.get_secret('CANVAS_API_SECRET')
            if canvas_key:
                self.canvas_api_key = canvas_key
            if canvas_secret:
                self.canvas_api_secret = canvas_secret
            
            # AI APIs
            openai_key = await secrets_manager.get_secret('OPENAI_API_KEY')
            google_key = await secrets_manager.get_secret('GOOGLE_API_KEY')
            if openai_key:
                self.openai_api_key = openai_key
            if google_key:
                self.google_api_key = google_key
            
            # Communication APIs
            twilio_token = await secrets_manager.get_secret('TWILIO_AUTH_TOKEN')
            telegram_token = await secrets_manager.get_secret('TELEGRAM_BOT_TOKEN')
            if twilio_token:
                self.twilio_auth_token = twilio_token
            if telegram_token:
                self.telegram_bot_token = telegram_token
            
            # Monitoring
            sentry_dsn = await secrets_manager.get_secret('SENTRY_DSN')
            if sentry_dsn:
                self.sentry_dsn = sentry_dsn
            
        except Exception as e:
            logger.error(f"Error loading external API config: {e}")
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value."""
        # Try cache first
        if key in self._secret_cache:
            return self._secret_cache[key]
        
        # Get from secrets manager
        value = await secrets_manager.get_secret(key)
        if value:
            self._secret_cache[key] = value
        
        return value
    
    async def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate a secret value."""
        success = await secrets_manager.rotate_secret(key, new_value)
        if success:
            # Update cache
            self._secret_cache[key] = new_value
            # Update settings attribute if it exists
            if hasattr(self, key.lower()):
                setattr(self, key.lower(), new_value)
        return success
    
    def mask_sensitive_value(self, value: str) -> str:
        """Mask sensitive values for logging."""
        if not value or len(value) < 8:
            return "***"
        return value[:3] + "***" + value[-3:]
    
    def get_safe_config_dict(self) -> Dict[str, Any]:
        """Get configuration dictionary with sensitive values masked."""
        config = self.dict()
        sensitive_keys = [
            'database_url', 'redis_url', 'secret_key', 'jwt_secret_key',
            'canvas_api_key', 'canvas_api_secret', 'openai_api_key',
            'google_api_key', 'twilio_auth_token', 'telegram_bot_token',
            'sentry_dsn', 'email_host_password', 'aws_secret_access_key'
        ]
        
        for key in sensitive_keys:
            if key in config and config[key]:
                config[key] = self.mask_sensitive_value(str(config[key]))
        
        return config


class SecurityManager:
    """Manager for security-related operations."""
    
    def __init__(self, settings: SecureSettings):
        self.settings = settings
    
    async def validate_secrets(self) -> Dict[str, bool]:
        """Validate that all required secrets are available."""
        required_secrets = [
            'SECRET_KEY',
            'DATABASE_URL',
            'JWT_SECRET_KEY'
        ]
        
        validation_results = {}
        
        for secret_key in required_secrets:
            value = await self.settings.get_secret(secret_key)
            validation_results[secret_key] = value is not None
            
            if not value:
                logger.warning(f"Required secret {secret_key} is not available")
        
        return validation_results
    
    async def rotate_jwt_secret(self) -> bool:
        """Rotate JWT secret key."""
        import secrets
        new_secret = secrets.token_urlsafe(32)
        success = await self.settings.rotate_secret('JWT_SECRET_KEY', new_secret)
        
        if success:
            logger.info("JWT secret key rotated successfully")
        else:
            logger.error("Failed to rotate JWT secret key")
        
        return success
    
    async def rotate_encryption_key(self) -> bool:
        """Rotate encryption key."""
        import secrets
        new_key = secrets.token_urlsafe(32)
        success = await self.settings.rotate_secret('ENCRYPTION_KEY', new_key)
        
        if success:
            logger.info("Encryption key rotated successfully")
        else:
            logger.error("Failed to rotate encryption key")
        
        return success
    
    async def check_secret_health(self) -> Dict[str, Any]:
        """Check the health of secrets management system."""
        health_status = {
            "secrets_manager_available": True,
            "backend_status": {},
            "required_secrets_present": {},
            "last_check": asyncio.get_event_loop().time()
        }
        
        try:
            # Check if secrets manager is working
            test_secret = await secrets_manager.get_secret('SECRET_KEY')
            health_status["secrets_manager_available"] = test_secret is not None
            
            # Check available backends
            for backend in secrets_manager.backends:
                health_status["backend_status"][backend.value] = True
            
            # Validate required secrets
            validation_results = await self.validate_secrets()
            health_status["required_secrets_present"] = validation_results
            
            # Overall health
            all_required_present = all(validation_results.values())
            health_status["healthy"] = (
                health_status["secrets_manager_available"] and 
                all_required_present
            )
            
        except Exception as e:
            logger.error(f"Error checking secret health: {e}")
            health_status["healthy"] = False
            health_status["error"] = str(e)
        
        return health_status
    
    async def audit_secret_access(self) -> Dict[str, Any]:
        """Audit secret access and usage."""
        # This would typically integrate with audit logging
        audit_info = {
            "total_secrets": len(secrets_manager._secret_cache) if hasattr(secrets_manager, '_secret_cache') else 0,
            "backends_in_use": list(secrets_manager.backends.keys()),
            "default_backend": secrets_manager.default_backend.value,
            "audit_timestamp": asyncio.get_event_loop().time()
        }
        
        return audit_info


# Function to create secure settings instance
async def create_secure_settings() -> SecureSettings:
    """Create and initialize secure settings."""
    settings = SecureSettings()
    await settings.load_secrets()
    return settings


# Cached function to get security manager
@lru_cache()
def get_security_manager() -> SecurityManager:
    """Get security manager instance."""
    # This will be initialized properly during app startup
    return SecurityManager(SecureSettings())
