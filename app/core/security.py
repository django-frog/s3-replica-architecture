import time
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import requests
from typing import Dict, Any
from app.core.config import settings

# Tells FastAPI to look for the Authorization header in incoming requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- NEW: In-Memory TTL Cache ---
JWKS_CACHE: Dict[str, Any] = {}
JWKS_TTL_SECONDS = 3600  # Cache keys for 1 hour

def get_public_key() -> dict:
    current_time = time.time()

    # 1. Return cached keys if they exist and are not expired
    if "keys" in JWKS_CACHE and (current_time - JWKS_CACHE.get("timestamp", 0)) < JWKS_TTL_SECONDS:
        return JWKS_CACHE["keys"]

    try:
        # The Discovery URL for the JWKS (JSON Web Key Set)
        jwks_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"

        # Adding a timeout is crucial to prevent the sync request from hanging the async worker indefinitely
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()

        keys = response.json()

        # 2. Update the cache with fresh keys and the current timestamp
        JWKS_CACHE["keys"] = keys
        JWKS_CACHE["timestamp"] = current_time

        return keys

    except Exception as e:
        print(f"Failed to fetch public keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Identity Provider is unreachable."
        )

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # JWKS is now pulled instantly from RAM 99% of the time
        jwks = get_public_key()

        # python-jose automatically matches the 'kid' (Key ID) in the token
        # to the correct RSA key inside the jwks dictionary!
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.KEYCLOAK_CLIENT_ID,
            issuer=settings.keycloak_issuer,
            options={
                "verify_iss": True,
                "verify_aud": True,
                # It's also best practice to enforce expiration checks
                "verify_exp": True
            }
        )

        username = payload.get("preferred_username")
        realm_access = payload.get("realm_access", {})
        roles = realm_access.get("roles", [])

        if username is None:
            raise credentials_exception

        return {
            "username": username,
            "roles": roles
        }

    except JWTError as e:
        print(f"Token signature validation failed: {str(e)}")
        raise credentials_exception
