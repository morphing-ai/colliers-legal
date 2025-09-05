# backend/app/api/auth.py
import os
import logging
from typing import Optional, Dict, Any, List
import httpx
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, jwk
from jose.utils import base64url_decode

from app.config import settings

logger = logging.getLogger(__name__)

# Create a security scheme for JWT bearer tokens
security = HTTPBearer(auto_error=False)  # False to handle missing tokens gracefully

class User(BaseModel):
    """User model from JWT claims."""
    id: str
    email: str
    name: Optional[str] = None
    
    @classmethod
    def from_claims(cls, claims: Dict[str, Any]) -> "User":
        """Create a User instance from JWT claims."""
        return cls(
            id=claims.get("sub"),
            email=claims.get("email", ""),
            name=claims.get("name", "")
        )

class AuthService:
    """Service for handling authentication and authorization"""
    
    def __init__(self):
        """Initialize the auth service"""
        self.clerk_pem_public_key = self._load_public_key()
        self.whitelist_email = self._parse_whitelist_emails()
        logger.info(f"Auth service initialized with whitelist: {self.whitelist_email}")
    
    def _load_public_key(self) -> Optional[str]:
        """Load the Clerk public key for JWT verification."""
        if settings.CLERK_PEM_PUBLIC_KEY:
            logger.info("Using PEM public key from settings")
            return settings.CLERK_PEM_PUBLIC_KEY
            
        pem_path = os.environ.get("CLERK_PEM_PUBLIC_KEY_PATH")
        if pem_path and os.path.exists(pem_path):
            try:
                with open(pem_path, "r") as key_file:
                    key_content = key_file.read()
                    logger.info(f"Loaded Clerk public key from file ({len(key_content)} bytes)")
                    return key_content
            except Exception as e:
                logger.error(f"Error loading Clerk public key: {str(e)}")
        
        logger.warning("No Clerk public key found, will use API verification")
        return None
    
    def _parse_whitelist_emails(self) -> List[str]:
        """Parse the whitelist email environment variable."""
        whitelist = settings.CLERK_WHITELIST_EMAIL
        if not whitelist:
            logger.warning("No email whitelist configured, all authenticated users will be allowed")
            return []
        
        whitelist_emails = [email.strip() for email in whitelist.split(",")]
        return whitelist_emails
    
    def _is_email_whitelisted(self, email: str) -> bool:
        """Check if an email is in the whitelist."""
        if not self.whitelist_email:
            # If no whitelist is configured, allow all emails
            return True
        
        # Check direct matches
        if email in self.whitelist_email:
            return True
        
        # Check domain wildcard matches (e.g., *.example.com)
        domain = email.split('@')[-1]
        for whitelisted in self.whitelist_email:
            if whitelisted.startswith('*.') and domain.endswith(whitelisted[2:]):
                return True
        
        return False

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token and return claims."""
        try:
            # First try to verify with PEM key if available
            if self.clerk_pem_public_key:
                try:
                    # Set up decode options
                    decode_options = {
                        "algorithms": ["RS256"],
                        "options": {"verify_exp": True, "leeway": 3600, "verify_iss": False,  }  # 10 minutes of leeway
                    }
                    
                    # Only add issuer validation if configured
                    if settings.CLERK_ISSUER:
                        decode_options["issuer"] = settings.CLERK_ISSUER
                    
                    # Note: Not using audience validation to match original implementation
                    
                    payload = jwt.decode(
                        token, 
                        self.clerk_pem_public_key,
                        **decode_options
                    )
                    logger.info(f"Token verification successful with PEM key. User: {payload.get('email')}")
                    return payload
                except Exception as e:
                    logger.error(f"Error verifying token with PEM key: {str(e)}")
                    # Fall through to API verification
            
            # If PEM key verification failed or not available, use Clerk's API
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
                    "Content-Type": "application/json"
                }
                
                # Call Clerk's verify endpoint
                response = await client.post(
                    "https://api.clerk.com/v1/tokens/verify",
                    headers=headers,
                    json={"token": token}
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token"
                    )
                
                claims = response.json().get("payload", {})
                logger.info(f"Token verification successful with Clerk API. User: {claims.get('email')}")
                return claims
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_token_from_request(
        self, 
        request: Request, 
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> str:
        """Get JWT token from request (either from Authorization header or session cookie)."""
        # First try the Authorization header
        if credentials and credentials.credentials:
            return credentials.credentials
            
        # Then try the session cookie
        token = request.cookies.get("__session")
        if token:
            return token
        
        # Development mode bypass if enabled
        if settings.DEBUG and os.environ.get("DEV_MODE", "").lower() == "true":
            logger.warning("DEV_MODE enabled - bypassing authentication")
            return "dev_mode_token"
            
        # No token found
        logger.warning("No authentication token found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async def get_user_from_token(self, payload: Dict[str, Any]) -> User:
        """Extract user info from JWT payload and check whitelist."""
        email = payload.get("email")
        if not email:
            logger.warning("JWT token missing email claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check whitelist
        if not self._is_email_whitelisted(email):
            logger.warning(f"Email not in whitelist: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied - email not authorized",
            )
        
        return User.from_claims(payload)

    async def get_current_user(
        self, 
        request: Request, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> User:
        """FastAPI dependency for getting the currently authenticated user."""
        # Development mode bypass
        if settings.DEBUG and os.environ.get("DEV_MODE", "").lower() == "true":
            logger.warning("DEV_MODE enabled - returning dev user")
            return User(id="dev_user_id", email="dev@example.com", name="Development User")
        
        token = await self.get_token_from_request(request, credentials)
        payload = await self.verify_token(token)
        user = await self.get_user_from_token(payload)
        
        # Store in request state for potential reuse
        request.state.user = user
        
        return user

# Create singleton instance
auth_service = AuthService()

# Export dependency for convenience
get_current_user = auth_service.get_current_user

# Backward compatibility with existing code
async def get_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Legacy dependency for compatibility with existing code."""
    request = Request(scope={"type": "http"})
    return await auth_service.get_current_user(request, credentials)