"""
LTI 1.3 (Learning Tools Interoperability) service implementation.

Handles LTI 1.3 OIDC login, Deep Linking, and Assignment and Grade Services (AGS).
"""

import logging
import json
import jwt
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urlencode, parse_qs, urlparse
import httpx

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, and_
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LTIPlatform:
    """LTI Platform configuration."""
    platform_id: str
    client_id: str
    deployment_id: str
    key_set_url: str
    auth_token_url: str
    auth_login_url: str
    target_link_uri: str
    public_key: Optional[str] = None
    private_key: Optional[str] = None
    issuer: Optional[str] = None


@dataclass
class LTILaunchData:
    """LTI Launch data from platform."""
    message_type: str
    version: str
    deployment_id: str
    target_link_uri: str
    resource_link_id: str
    context_id: Optional[str] = None
    context_title: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    roles: Optional[List[str]] = None
    custom_params: Optional[Dict[str, Any]] = None
    launch_presentation: Optional[Dict[str, Any]] = None


@dataclass
class DeepLinkingRequest:
    """Deep Linking request data."""
    deep_linking_settings: Dict[str, Any]
    accept_types: List[str]
    accept_presentation_document_targets: List[str]
    accept_media_types: Optional[List[str]] = None
    auto_create: Optional[bool] = None
    title: Optional[str] = None
    text: Optional[str] = None


@dataclass
class ContentItem:
    """Content item for Deep Linking response."""
    type: str  # "ltiResourceLink", "link", "file", "html"
    title: str
    url: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None
    lineItem: Optional[Dict[str, Any]] = None
    available: Optional[Dict[str, str]] = None
    submission: Optional[Dict[str, str]] = None


class LTI13Service:
    """LTI 1.3 service implementation."""
    
    def __init__(self):
        self.platforms: Dict[str, LTIPlatform] = {}
        self.private_key = None
        self.public_key = None
        self.key_id = "eduanalytics-key-1"
        
    async def initialize(self):
        """Initialize LTI service."""
        try:
            # Generate or load RSA key pair
            await self._setup_keys()
            
            # Load platform configurations
            await self._load_platforms()
            
            # Create database tables
            async with AsyncSessionLocal() as db:
                await self._create_lti_tables(db)
            
            logger.info("LTI 1.3 service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing LTI service: {e}")
            raise
    
    async def _setup_keys(self):
        """Setup RSA key pair for JWT signing."""
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            
            # Serialize private key
            self.private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            # Serialize public key
            public_key = private_key.public_key()
            self.public_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            logger.info("RSA key pair generated for LTI")
            
        except Exception as e:
            logger.error(f"Error setting up LTI keys: {e}")
            raise
    
    async def _load_platforms(self):
        """Load LTI platform configurations."""
        try:
            # Canvas platform configuration
            canvas_platform = LTIPlatform(
                platform_id="https://canvas.instructure.com",
                client_id=settings.CANVAS_CLIENT_ID if hasattr(settings, 'CANVAS_CLIENT_ID') else "your-client-id",
                deployment_id="1:your-deployment-id",
                key_set_url="https://canvas.instructure.com/api/lti/security/jwks",
                auth_token_url="https://canvas.instructure.com/login/oauth2/token",
                auth_login_url="https://canvas.instructure.com/api/lti/authorize_redirect",
                target_link_uri=f"{settings.BASE_URL}/api/lti/launch",
                issuer="https://canvas.instructure.com"
            )
            
            self.platforms[canvas_platform.platform_id] = canvas_platform
            
            # Add more platforms as needed
            logger.info(f"Loaded {len(self.platforms)} LTI platforms")
            
        except Exception as e:
            logger.error(f"Error loading LTI platforms: {e}")
    
    async def _create_lti_tables(self, db: AsyncSession):
        """Create LTI-related database tables."""
        create_tables_sql = """
        -- LTI launches table
        CREATE TABLE IF NOT EXISTS lti_launches (
            launch_id VARCHAR(255) PRIMARY KEY,
            platform_id VARCHAR(255) NOT NULL,
            deployment_id VARCHAR(255) NOT NULL,
            user_id VARCHAR(255),
            context_id VARCHAR(255),
            resource_link_id VARCHAR(255) NOT NULL,
            message_type VARCHAR(100) NOT NULL,
            target_link_uri TEXT NOT NULL,
            launch_data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_lti_launches_platform ON lti_launches(platform_id);
        CREATE INDEX IF NOT EXISTS idx_lti_launches_user ON lti_launches(user_id);
        CREATE INDEX IF NOT EXISTS idx_lti_launches_context ON lti_launches(context_id);
        CREATE INDEX IF NOT EXISTS idx_lti_launches_expires ON lti_launches(expires_at);
        
        -- LTI nonces table (for security)
        CREATE TABLE IF NOT EXISTS lti_nonces (
            nonce VARCHAR(255) PRIMARY KEY,
            platform_id VARCHAR(255) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_lti_nonces_expires ON lti_nonces(expires_at);
        
        -- LTI content items table (for Deep Linking)
        CREATE TABLE IF NOT EXISTS lti_content_items (
            item_id SERIAL PRIMARY KEY,
            platform_id VARCHAR(255) NOT NULL,
            deployment_id VARCHAR(255) NOT NULL,
            context_id VARCHAR(255),
            item_type VARCHAR(50) NOT NULL,
            title VARCHAR(255) NOT NULL,
            url TEXT,
            content_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_lti_content_items_platform ON lti_content_items(platform_id);
        CREATE INDEX IF NOT EXISTS idx_lti_content_items_context ON lti_content_items(context_id);
        
        -- LTI line items table (for AGS)
        CREATE TABLE IF NOT EXISTS lti_line_items (
            line_item_id SERIAL PRIMARY KEY,
            platform_id VARCHAR(255) NOT NULL,
            context_id VARCHAR(255) NOT NULL,
            resource_link_id VARCHAR(255),
            label VARCHAR(255) NOT NULL,
            score_maximum DECIMAL(10,2),
            resource_id VARCHAR(255),
            tag VARCHAR(255),
            start_date_time TIMESTAMP WITH TIME ZONE,
            end_date_time TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_lti_line_items_platform ON lti_line_items(platform_id);
        CREATE INDEX IF NOT EXISTS idx_lti_line_items_context ON lti_line_items(context_id);
        """
        
        await db.execute(text(create_tables_sql))
        await db.commit()
    
    async def handle_oidc_login(self, request_data: Dict[str, Any]) -> str:
        """Handle OIDC login initiation."""
        try:
            # Extract required parameters
            iss = request_data.get('iss')  # issuer
            login_hint = request_data.get('login_hint')
            target_link_uri = request_data.get('target_link_uri')
            client_id = request_data.get('client_id')
            deployment_id = request_data.get('lti_deployment_id')
            
            if not all([iss, login_hint, target_link_uri, client_id]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required OIDC login parameters"
                )
            
            # Find platform configuration
            platform = self.platforms.get(iss)
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown platform: {iss}"
                )
            
            # Generate state and nonce
            state = str(uuid.uuid4())
            nonce = str(uuid.uuid4())
            
            # Store nonce for verification
            await self._store_nonce(nonce, iss)
            
            # Build authorization redirect URL
            auth_params = {
                'response_type': 'id_token',
                'client_id': client_id,
                'redirect_uri': target_link_uri,
                'login_hint': login_hint,
                'state': state,
                'response_mode': 'form_post',
                'nonce': nonce,
                'prompt': 'none',
                'scope': 'openid'
            }
            
            if deployment_id:
                auth_params['lti_deployment_id'] = deployment_id
            
            auth_url = f"{platform.auth_login_url}?{urlencode(auth_params)}"
            
            logger.info(f"OIDC login redirect generated for platform: {iss}")
            return auth_url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling OIDC login: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OIDC login failed: {str(e)}"
            )
    
    async def handle_lti_launch(self, id_token: str, state: str) -> LTILaunchData:
        """Handle LTI launch with ID token."""
        try:
            # Decode JWT without verification first to get header info
            unverified_payload = jwt.decode(id_token, options={"verify_signature": False})
            
            # Get issuer and key ID
            iss = unverified_payload.get('iss')
            header = jwt.get_unverified_header(id_token)
            kid = header.get('kid')
            
            # Find platform
            platform = self.platforms.get(iss)
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown platform: {iss}"
                )
            
            # Get platform's public key
            public_key = await self._get_platform_public_key(platform, kid)
            
            # Verify and decode JWT
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=platform.client_id,
                issuer=iss
            )
            
            # Verify nonce
            nonce = payload.get('nonce')
            if not await self._verify_nonce(nonce, iss):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired nonce"
                )
            
            # Extract LTI launch data
            launch_data = self._extract_launch_data(payload)
            
            # Store launch for session management
            launch_id = str(uuid.uuid4())
            await self._store_launch(launch_id, platform.platform_id, launch_data, payload)
            
            logger.info(f"LTI launch successful for user: {launch_data.user_id}")
            return launch_data
            
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling LTI launch: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"LTI launch failed: {str(e)}"
            )
    
    async def handle_deep_linking_request(self, launch_data: LTILaunchData) -> DeepLinkingRequest:
        """Handle Deep Linking request."""
        try:
            if launch_data.message_type != "LtiDeepLinkingRequest":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Not a Deep Linking request"
                )
            
            # Extract Deep Linking settings from custom params
            dl_settings = launch_data.custom_params.get('deep_linking_settings', {})
            
            deep_linking_request = DeepLinkingRequest(
                deep_linking_settings=dl_settings,
                accept_types=dl_settings.get('accept_types', ['ltiResourceLink']),
                accept_presentation_document_targets=dl_settings.get(
                    'accept_presentation_document_targets', ['iframe']
                ),
                accept_media_types=dl_settings.get('accept_media_types'),
                auto_create=dl_settings.get('auto_create', False),
                title=dl_settings.get('title'),
                text=dl_settings.get('text')
            )
            
            return deep_linking_request
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error handling Deep Linking request: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deep Linking request failed: {str(e)}"
            )
    
    async def create_deep_linking_response(
        self, 
        platform_id: str,
        deployment_id: str,
        content_items: List[ContentItem],
        return_url: str
    ) -> str:
        """Create Deep Linking response JWT."""
        try:
            platform = self.platforms.get(platform_id)
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown platform: {platform_id}"
                )
            
            # Build JWT payload
            now = int(time.time())
            payload = {
                'iss': f"{settings.BASE_URL}",
                'aud': platform.client_id,
                'exp': now + 300,  # 5 minutes
                'iat': now,
                'nonce': str(uuid.uuid4()),
                'https://purl.imsglobal.org/spec/lti/claim/message_type': 'LtiDeepLinkingResponse',
                'https://purl.imsglobal.org/spec/lti/claim/version': '1.3.0',
                'https://purl.imsglobal.org/spec/lti/claim/deployment_id': deployment_id,
                'https://purl.imsglobal.org/spec/lti-dl/claim/content_items': [
                    asdict(item) for item in content_items
                ]
            }
            
            # Sign JWT with our private key
            jwt_token = jwt.encode(
                payload,
                self.private_key,
                algorithm='RS256',
                headers={'kid': self.key_id}
            )
            
            return jwt_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating Deep Linking response: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deep Linking response failed: {str(e)}"
            )
    
    async def get_available_content_items(self, context_id: Optional[str] = None) -> List[ContentItem]:
        """Get available content items for Deep Linking."""
        try:
            # This would typically query your content database
            # For now, return some example content items
            
            content_items = [
                ContentItem(
                    type="ltiResourceLink",
                    title="Course Analytics Dashboard",
                    url=f"{settings.BASE_URL}/api/lti/content/analytics",
                    text="View comprehensive analytics for your course",
                    custom={
                        "content_type": "analytics",
                        "features": ["grades", "engagement", "predictions"]
                    }
                ),
                ContentItem(
                    type="ltiResourceLink",
                    title="AI-Powered Study Assistant",
                    url=f"{settings.BASE_URL}/api/lti/content/ai-assistant",
                    text="Get AI-powered help with course content",
                    custom={
                        "content_type": "ai_assistant",
                        "features": ["chat", "recommendations", "study_plans"]
                    }
                ),
                ContentItem(
                    type="ltiResourceLink",
                    title="Interactive Quiz Engine",
                    url=f"{settings.BASE_URL}/api/lti/content/quiz",
                    text="Create and take interactive quizzes",
                    custom={
                        "content_type": "quiz",
                        "features": ["adaptive", "analytics", "feedback"]
                    },
                    lineItem={
                        "scoreMaximum": 100,
                        "label": "Quiz Score",
                        "resourceId": "quiz-engine"
                    }
                ),
                ContentItem(
                    type="link",
                    title="Student Performance Report",
                    url=f"{settings.BASE_URL}/reports/performance",
                    text="Detailed performance analytics and insights"
                )
            ]
            
            return content_items
            
        except Exception as e:
            logger.error(f"Error getting content items: {e}")
            return []
    
    async def _get_platform_public_key(self, platform: LTIPlatform, kid: Optional[str] = None) -> str:
        """Get platform's public key from JWKS endpoint."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(platform.key_set_url)
                response.raise_for_status()
                
                jwks = response.json()
                keys = jwks.get('keys', [])
                
                # Find key by kid or use first available
                target_key = None
                if kid:
                    target_key = next((k for k in keys if k.get('kid') == kid), None)
                
                if not target_key and keys:
                    target_key = keys[0]
                
                if not target_key:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="No suitable public key found"
                    )
                
                # Convert JWK to PEM format
                from jwt.algorithms import RSAAlgorithm
                public_key = RSAAlgorithm.from_jwk(json.dumps(target_key))
                
                return public_key
                
        except Exception as e:
            logger.error(f"Error getting platform public key: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve platform public key"
            )
    
    def _extract_launch_data(self, payload: Dict[str, Any]) -> LTILaunchData:
        """Extract LTI launch data from JWT payload."""
        return LTILaunchData(
            message_type=payload.get('https://purl.imsglobal.org/spec/lti/claim/message_type', ''),
            version=payload.get('https://purl.imsglobal.org/spec/lti/claim/version', ''),
            deployment_id=payload.get('https://purl.imsglobal.org/spec/lti/claim/deployment_id', ''),
            target_link_uri=payload.get('https://purl.imsglobal.org/spec/lti/claim/target_link_uri', ''),
            resource_link_id=payload.get('https://purl.imsglobal.org/spec/lti/claim/resource_link', {}).get('id', ''),
            context_id=payload.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('id'),
            context_title=payload.get('https://purl.imsglobal.org/spec/lti/claim/context', {}).get('title'),
            user_id=payload.get('sub'),
            user_name=payload.get('name'),
            user_email=payload.get('email'),
            roles=payload.get('https://purl.imsglobal.org/spec/lti/claim/roles', []),
            custom_params=payload.get('https://purl.imsglobal.org/spec/lti/claim/custom', {}),
            launch_presentation=payload.get('https://purl.imsglobal.org/spec/lti/claim/launch_presentation', {})
        )
    
    async def _store_nonce(self, nonce: str, platform_id: str):
        """Store nonce for verification."""
        try:
            async with AsyncSessionLocal() as db:
                expires_at = datetime.utcnow() + timedelta(minutes=5)
                
                insert_sql = """
                INSERT INTO lti_nonces (nonce, platform_id, expires_at)
                VALUES (:nonce, :platform_id, :expires_at)
                """
                
                await db.execute(text(insert_sql), {
                    "nonce": nonce,
                    "platform_id": platform_id,
                    "expires_at": expires_at
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing nonce: {e}")
    
    async def _verify_nonce(self, nonce: str, platform_id: str) -> bool:
        """Verify and consume nonce."""
        try:
            async with AsyncSessionLocal() as db:
                # Check if nonce exists and is valid
                select_sql = """
                SELECT 1 FROM lti_nonces 
                WHERE nonce = :nonce AND platform_id = :platform_id AND expires_at > NOW()
                """
                
                result = await db.execute(text(select_sql), {
                    "nonce": nonce,
                    "platform_id": platform_id
                })
                
                if not result.fetchone():
                    return False
                
                # Delete nonce (one-time use)
                delete_sql = """
                DELETE FROM lti_nonces 
                WHERE nonce = :nonce AND platform_id = :platform_id
                """
                
                await db.execute(text(delete_sql), {
                    "nonce": nonce,
                    "platform_id": platform_id
                })
                
                await db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error verifying nonce: {e}")
            return False
    
    async def _store_launch(self, launch_id: str, platform_id: str, 
                          launch_data: LTILaunchData, full_payload: Dict[str, Any]):
        """Store launch data for session management."""
        try:
            async with AsyncSessionLocal() as db:
                expires_at = datetime.utcnow() + timedelta(hours=24)
                
                insert_sql = """
                INSERT INTO lti_launches (
                    launch_id, platform_id, deployment_id, user_id, context_id,
                    resource_link_id, message_type, target_link_uri, launch_data, expires_at
                ) VALUES (
                    :launch_id, :platform_id, :deployment_id, :user_id, :context_id,
                    :resource_link_id, :message_type, :target_link_uri, :launch_data, :expires_at
                )
                """
                
                await db.execute(text(insert_sql), {
                    "launch_id": launch_id,
                    "platform_id": platform_id,
                    "deployment_id": launch_data.deployment_id,
                    "user_id": launch_data.user_id,
                    "context_id": launch_data.context_id,
                    "resource_link_id": launch_data.resource_link_id,
                    "message_type": launch_data.message_type,
                    "target_link_uri": launch_data.target_link_uri,
                    "launch_data": json.dumps(full_payload),
                    "expires_at": expires_at
                })
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"Error storing launch: {e}")
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up expired LTI data."""
        try:
            async with AsyncSessionLocal() as db:
                cleanup_counts = {}
                
                # Clean up expired nonces
                result = await db.execute(text("DELETE FROM lti_nonces WHERE expires_at <= NOW()"))
                cleanup_counts["nonces"] = result.rowcount
                
                # Clean up expired launches
                result = await db.execute(text("DELETE FROM lti_launches WHERE expires_at <= NOW()"))
                cleanup_counts["launches"] = result.rowcount
                
                await db.commit()
                
                total_cleaned = sum(cleanup_counts.values())
                if total_cleaned > 0:
                    logger.info(f"LTI cleanup: {cleanup_counts}")
                
                return cleanup_counts
                
        except Exception as e:
            logger.error(f"Error cleaning up LTI data: {e}")
            return {}
    
    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set for platform verification."""
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            import base64
            
            # Load public key
            public_key = load_pem_public_key(self.public_key.encode())
            
            # Get key components
            numbers = public_key.public_numbers()
            
            # Convert to base64url encoding
            def int_to_base64url(value):
                byte_length = (value.bit_length() + 7) // 8
                return base64.urlsafe_b64encode(
                    value.to_bytes(byte_length, 'big')
                ).decode('ascii').rstrip('=')
            
            jwk = {
                "kty": "RSA",
                "use": "sig",
                "kid": self.key_id,
                "alg": "RS256",
                "n": int_to_base64url(numbers.n),
                "e": int_to_base64url(numbers.e)
            }
            
            return {
                "keys": [jwk]
            }
            
        except Exception as e:
            logger.error(f"Error generating JWKS: {e}")
            return {"keys": []}


# Global LTI service instance
lti_service = LTI13Service()
