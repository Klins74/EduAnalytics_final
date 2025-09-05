"""API routes for security and secrets management."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.core.security import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.secrets_manager import secrets_manager, SecretBackend
from app.core.security_config import get_security_manager

router = APIRouter(prefix="/security", tags=["Security"])


class SecretRequest(BaseModel):
    key: str
    value: str
    backend: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SecretResponse(BaseModel):
    key: str
    backend: str
    masked_value: str
    metadata: Optional[Dict[str, Any]] = None


class SecretRotationRequest(BaseModel):
    key: str
    new_value: str


class HealthResponse(BaseModel):
    healthy: bool
    details: Dict[str, Any]


@router.get("/health", response_model=HealthResponse, summary="Check security system health")
async def check_security_health(
    current_user: User = Depends(require_role(UserRole.admin))
) -> HealthResponse:
    """Check the health of the security and secrets management system."""
    try:
        security_manager = get_security_manager()
        health_details = await security_manager.check_secret_health()
        
        return HealthResponse(
            healthy=health_details.get("healthy", False),
            details=health_details
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check security health: {str(e)}"
        )


@router.get("/secrets/backends", summary="List available secret backends")
async def list_secret_backends(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """List all available secret management backends."""
    try:
        available_backends = []
        
        for backend in secrets_manager.backends:
            backend_info = {
                "name": backend.value,
                "available": backend in secrets_manager.backends,
                "is_default": backend == secrets_manager.default_backend
            }
            available_backends.append(backend_info)
        
        return {
            "backends": available_backends,
            "default_backend": secrets_manager.default_backend.value,
            "total_backends": len(secrets_manager.backends)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backends: {str(e)}"
        )


@router.get("/secrets", summary="List secrets (masked values)")
async def list_secrets(
    backend: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, List[SecretResponse]]:
    """List all secrets with masked values."""
    try:
        secret_backend = None
        if backend:
            try:
                secret_backend = SecretBackend(backend)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid backend: {backend}"
                )
        
        secrets = await secrets_manager.list_secrets(secret_backend)
        
        secret_list = []
        for key, secret_info in secrets.items():
            secret_list.append(SecretResponse(
                key=key,
                backend=secret_info.backend.value,
                masked_value=secret_info.value,  # Already masked
                metadata=secret_info.metadata
            ))
        
        return {
            "secrets": secret_list,
            "backend": backend or secrets_manager.default_backend.value,
            "total": len(secret_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list secrets: {str(e)}"
        )


@router.post("/secrets", summary="Create or update a secret")
async def create_secret(
    secret_request: SecretRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Create or update a secret in the specified backend."""
    try:
        backend = None
        if secret_request.backend:
            try:
                backend = SecretBackend(secret_request.backend)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid backend: {secret_request.backend}"
                )
        
        success = await secrets_manager.set_secret(
            key=secret_request.key,
            value=secret_request.value,
            backend=backend,
            metadata=secret_request.metadata
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create/update secret"
            )
        
        return {
            "message": f"Secret '{secret_request.key}' created/updated successfully",
            "key": secret_request.key,
            "backend": backend.value if backend else secrets_manager.default_backend.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create secret: {str(e)}"
        )


@router.post("/secrets/{key}/rotate", summary="Rotate a secret value")
async def rotate_secret(
    key: str,
    rotation_request: SecretRotationRequest,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Rotate a secret by updating its value."""
    try:
        if rotation_request.key != key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Key in URL must match key in request body"
            )
        
        success = await secrets_manager.rotate_secret(key, rotation_request.new_value)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to rotate secret '{key}'"
            )
        
        return {
            "message": f"Secret '{key}' rotated successfully",
            "key": key,
            "rotated_at": "now"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate secret: {str(e)}"
        )


@router.delete("/secrets/{key}", summary="Delete a secret")
async def delete_secret(
    key: str,
    backend: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Delete a secret from the specified backend."""
    try:
        secret_backend = None
        if backend:
            try:
                secret_backend = SecretBackend(backend)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid backend: {backend}"
                )
        
        success = await secrets_manager.delete_secret(key, secret_backend)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret '{key}' not found or could not be deleted"
            )
        
        return {
            "message": f"Secret '{key}' deleted successfully",
            "key": key,
            "backend": backend or secrets_manager.default_backend.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete secret: {str(e)}"
        )


@router.get("/secrets/{key}/exists", summary="Check if a secret exists")
async def check_secret_exists(
    key: str,
    backend: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Check if a secret exists in the specified backend."""
    try:
        secret_backend = None
        if backend:
            try:
                secret_backend = SecretBackend(backend)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid backend: {backend}"
                )
        
        value = await secrets_manager.get_secret(key, secret_backend, fallback_to_env=False)
        exists = value is not None
        
        return {
            "key": key,
            "exists": exists,
            "backend": backend or secrets_manager.default_backend.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check secret existence: {str(e)}"
        )


@router.post("/jwt/rotate", summary="Rotate JWT secret key")
async def rotate_jwt_secret(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Rotate the JWT secret key."""
    try:
        security_manager = get_security_manager()
        success = await security_manager.rotate_jwt_secret()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rotate JWT secret"
            )
        
        return {
            "message": "JWT secret key rotated successfully",
            "rotated_at": "now",
            "warning": "All existing JWT tokens will be invalidated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate JWT secret: {str(e)}"
        )


@router.post("/encryption/rotate", summary="Rotate encryption key")
async def rotate_encryption_key(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Rotate the encryption key."""
    try:
        security_manager = get_security_manager()
        success = await security_manager.rotate_encryption_key()
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rotate encryption key"
            )
        
        return {
            "message": "Encryption key rotated successfully",
            "rotated_at": "now",
            "warning": "Previously encrypted data may need re-encryption"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rotate encryption key: {str(e)}"
        )


@router.get("/audit", summary="Get security audit information")
async def get_security_audit(
    current_user: User = Depends(require_role(UserRole.admin))
) -> Dict[str, Any]:
    """Get security audit information."""
    try:
        security_manager = get_security_manager()
        audit_info = await security_manager.audit_secret_access()
        
        # Add additional security metrics
        validation_results = await security_manager.validate_secrets()
        
        audit_info.update({
            "required_secrets_validation": validation_results,
            "admin_user": current_user.username,
            "audit_requested_at": "now"
        })
        
        return audit_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security audit: {str(e)}"
        )
