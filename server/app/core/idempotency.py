"""
Idempotency key system for safe POST/PUT operations.

Prevents duplicate operations by tracking idempotency keys and returning
cached responses for repeated requests.
"""

import logging
import json
import hashlib
from typing import Dict, Any, Optional, Union, Callable
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass, asdict

from fastapi import Request, Response, HTTPException, status, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_
import redis.asyncio as redis

from app.db.session import AsyncSessionLocal
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)


@dataclass
class IdempotencyRecord:
    """Idempotency record for tracking requests."""
    key: str
    request_hash: str
    response_status: int
    response_body: str
    response_headers: Dict[str, str]
    created_at: datetime
    expires_at: datetime
    endpoint: str
    user_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class IdempotencyKeyError(Exception):
    """Idempotency key related errors."""
    pass


class IdempotencyManager:
    """Manages idempotency keys and cached responses."""
    
    def __init__(self, default_ttl_minutes: int = 60):
        self.default_ttl_minutes = default_ttl_minutes
        self.redis_client = redis_service.get_client()
        self.key_prefix = "idempotency:"
    
    async def initialize(self):
        """Initialize idempotency system."""
        try:
            async with AsyncSessionLocal() as db:
                await self._create_idempotency_table(db)
            logger.info("Idempotency system initialized")
        except Exception as e:
            logger.error(f"Error initializing idempotency system: {e}")
            raise
    
    async def _create_idempotency_table(self, db: AsyncSession):
        """Create idempotency table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            key VARCHAR(255) PRIMARY KEY,
            request_hash VARCHAR(64) NOT NULL,
            response_status INTEGER NOT NULL,
            response_body TEXT NOT NULL,
            response_headers JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            endpoint VARCHAR(255) NOT NULL,
            user_id INTEGER,
            metadata JSONB,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_idempotency_expires_at ON idempotency_keys(expires_at);
        CREATE INDEX IF NOT EXISTS idx_idempotency_user_id ON idempotency_keys(user_id);
        CREATE INDEX IF NOT EXISTS idx_idempotency_endpoint ON idempotency_keys(endpoint);
        """
        
        await db.execute(text(create_table_sql))
        await db.commit()
    
    def generate_idempotency_key(self) -> str:
        """Generate a new idempotency key."""
        return str(uuid.uuid4())
    
    def _generate_request_hash(self, request: Request, body: bytes) -> str:
        """Generate hash of request for comparison."""
        hash_data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": sorted(request.query_params.items()),
            "body": body.hex() if body else ""
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def check_idempotency(
        self, 
        idempotency_key: str, 
        request: Request, 
        body: bytes,
        user_id: Optional[int] = None
    ) -> Optional[IdempotencyRecord]:
        """Check if request is idempotent and return cached response if available."""
        try:
            request_hash = self._generate_request_hash(request, body)
            
            # First check Redis cache
            cached_record = await self._get_from_cache(idempotency_key)
            if cached_record:
                # Verify request hash matches
                if cached_record.request_hash == request_hash:
                    return cached_record
                else:
                    # Same key but different request - this is an error
                    raise IdempotencyKeyError(
                        f"Idempotency key '{idempotency_key}' already used for different request"
                    )
            
            # Check database
            async with AsyncSessionLocal() as db:
                query = """
                SELECT key, request_hash, response_status, response_body, 
                       response_headers, created_at, expires_at, endpoint, user_id, metadata
                FROM idempotency_keys 
                WHERE key = :key AND expires_at > NOW()
                """
                
                result = await db.execute(text(query), {"key": idempotency_key})
                row = result.fetchone()
                
                if row:
                    record = IdempotencyRecord(
                        key=row.key,
                        request_hash=row.request_hash,
                        response_status=row.response_status,
                        response_body=row.response_body,
                        response_headers=json.loads(row.response_headers) if row.response_headers else {},
                        created_at=row.created_at,
                        expires_at=row.expires_at,
                        endpoint=row.endpoint,
                        user_id=row.user_id,
                        metadata=json.loads(row.metadata) if row.metadata else None
                    )
                    
                    # Verify request hash matches
                    if record.request_hash == request_hash:
                        # Cache in Redis for faster access
                        await self._store_in_cache(record)
                        return record
                    else:
                        # Same key but different request
                        raise IdempotencyKeyError(
                            f"Idempotency key '{idempotency_key}' already used for different request"
                        )
            
            return None
            
        except IdempotencyKeyError:
            raise
        except Exception as e:
            logger.error(f"Error checking idempotency: {e}")
            return None
    
    async def store_response(
        self, 
        idempotency_key: str, 
        request: Request, 
        body: bytes,
        response: Response,
        user_id: Optional[int] = None,
        ttl_minutes: Optional[int] = None
    ) -> bool:
        """Store response for idempotency key."""
        try:
            ttl = ttl_minutes or self.default_ttl_minutes
            expires_at = datetime.utcnow() + timedelta(minutes=ttl)
            request_hash = self._generate_request_hash(request, body)
            
            # Extract response data
            response_body = ""
            response_headers = {}
            
            if hasattr(response, 'body'):
                if isinstance(response.body, bytes):
                    response_body = response.body.decode('utf-8', errors='ignore')
                else:
                    response_body = str(response.body)
            
            if hasattr(response, 'headers'):
                response_headers = dict(response.headers)
            
            record = IdempotencyRecord(
                key=idempotency_key,
                request_hash=request_hash,
                response_status=response.status_code,
                response_body=response_body,
                response_headers=response_headers,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                endpoint=f"{request.method} {request.url.path}",
                user_id=user_id,
                metadata={
                    "content_type": response_headers.get("content-type"),
                    "content_length": len(response_body)
                }
            )
            
            # Store in database
            async with AsyncSessionLocal() as db:
                insert_sql = """
                INSERT INTO idempotency_keys (
                    key, request_hash, response_status, response_body, response_headers,
                    created_at, expires_at, endpoint, user_id, metadata
                ) VALUES (
                    :key, :request_hash, :response_status, :response_body, :response_headers,
                    :created_at, :expires_at, :endpoint, :user_id, :metadata
                ) ON CONFLICT (key) DO NOTHING
                """
                
                await db.execute(text(insert_sql), {
                    "key": record.key,
                    "request_hash": record.request_hash,
                    "response_status": record.response_status,
                    "response_body": record.response_body,
                    "response_headers": json.dumps(record.response_headers),
                    "created_at": record.created_at,
                    "expires_at": record.expires_at,
                    "endpoint": record.endpoint,
                    "user_id": record.user_id,
                    "metadata": json.dumps(record.metadata) if record.metadata else None
                })
                
                await db.commit()
            
            # Store in Redis cache
            await self._store_in_cache(record)
            
            logger.debug(f"Stored idempotency record for key: {idempotency_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing idempotency response: {e}")
            return False
    
    async def _get_from_cache(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        """Get idempotency record from Redis cache."""
        try:
            cache_key = f"{self.key_prefix}{idempotency_key}"
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return IdempotencyRecord(
                    key=data["key"],
                    request_hash=data["request_hash"],
                    response_status=data["response_status"],
                    response_body=data["response_body"],
                    response_headers=data["response_headers"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    expires_at=datetime.fromisoformat(data["expires_at"]),
                    endpoint=data["endpoint"],
                    user_id=data.get("user_id"),
                    metadata=data.get("metadata")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    async def _store_in_cache(self, record: IdempotencyRecord):
        """Store idempotency record in Redis cache."""
        try:
            cache_key = f"{self.key_prefix}{record.key}"
            cache_data = {
                "key": record.key,
                "request_hash": record.request_hash,
                "response_status": record.response_status,
                "response_body": record.response_body,
                "response_headers": record.response_headers,
                "created_at": record.created_at.isoformat(),
                "expires_at": record.expires_at.isoformat(),
                "endpoint": record.endpoint,
                "user_id": record.user_id,
                "metadata": record.metadata
            }
            
            # Calculate TTL in seconds
            ttl_seconds = int((record.expires_at - datetime.utcnow()).total_seconds())
            if ttl_seconds > 0:
                await self.redis_client.setex(
                    cache_key, 
                    ttl_seconds, 
                    json.dumps(cache_data, default=str)
                )
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
    
    async def cleanup_expired(self) -> int:
        """Clean up expired idempotency records."""
        try:
            async with AsyncSessionLocal() as db:
                delete_sql = "DELETE FROM idempotency_keys WHERE expires_at <= NOW()"
                result = await db.execute(text(delete_sql))
                await db.commit()
                
                deleted_count = result.rowcount
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired idempotency records")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up expired records: {e}")
            return 0
    
    async def get_user_keys(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get idempotency keys for a user."""
        try:
            async with AsyncSessionLocal() as db:
                query = """
                SELECT key, endpoint, created_at, expires_at, response_status
                FROM idempotency_keys
                WHERE user_id = :user_id AND expires_at > NOW()
                ORDER BY created_at DESC
                LIMIT :limit
                """
                
                result = await db.execute(text(query), {"user_id": user_id, "limit": limit})
                
                return [
                    {
                        "key": row.key,
                        "endpoint": row.endpoint,
                        "created_at": row.created_at.isoformat(),
                        "expires_at": row.expires_at.isoformat(),
                        "response_status": row.response_status
                    }
                    for row in result.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting user keys: {e}")
            return []


# Global idempotency manager instance
idempotency_manager = IdempotencyManager()


def require_idempotency_key(ttl_minutes: int = 60):
    """Decorator to require idempotency key for endpoint."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract request, user, and idempotency key from arguments
            request = None
            current_user = None
            idempotency_key = None
            
            # Find request object
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Find current user
            current_user = kwargs.get('current_user')
            
            # Get idempotency key from header
            if request:
                idempotency_key = request.headers.get("Idempotency-Key")
            
            if not idempotency_key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Idempotency-Key header is required for this operation",
                    headers={"X-Required-Header": "Idempotency-Key"}
                )
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Get request body
            body = await request.body()
            user_id = current_user.id if current_user else None
            
            # Check for existing idempotent response
            try:
                existing_record = await idempotency_manager.check_idempotency(
                    idempotency_key, request, body, user_id
                )
                
                if existing_record:
                    # Return cached response
                    return JSONResponse(
                        status_code=existing_record.response_status,
                        content=json.loads(existing_record.response_body) if existing_record.response_body else None,
                        headers={
                            **existing_record.response_headers,
                            "X-Idempotency-Replay": "true",
                            "X-Idempotency-Key": idempotency_key
                        }
                    )
                
            except IdempotencyKeyError as e:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e)
                )
            
            # Execute the original function
            response = await func(*args, **kwargs)
            
            # Store response for future idempotent requests
            if isinstance(response, (Response, JSONResponse)):
                await idempotency_manager.store_response(
                    idempotency_key, request, body, response, user_id, ttl_minutes
                )
                
                # Add idempotency headers
                if hasattr(response, 'headers'):
                    response.headers["X-Idempotency-Key"] = idempotency_key
                    response.headers["X-Idempotency-Replay"] = "false"
            
            return response
        
        return wrapper
    return decorator


# Dependency for getting idempotency key from header
async def get_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """Get idempotency key from request header."""
    return idempotency_key


# Dependency for requiring idempotency key
async def require_idempotency_key_dependency(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> str:
    """Require idempotency key from request header."""
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
            headers={"X-Required-Header": "Idempotency-Key"}
        )
    return idempotency_key
