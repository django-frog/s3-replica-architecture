from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import requests
from typing import Dict, Any
from app.core.config import settings

# Tells FastAPI to look for the Authorization header in incoming requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_public_key() -> dict:
    try:
        # The Discovery URL for the JWKS (JSON Web Key Set)
        jwks_url = f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
        response = requests.get(jwks_url)
        response.raise_for_status()

        # Return the ENTIRE dictionary instead of guessing keys[0]
        return response.json()
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
        # jwks is now the full Keycloak dictionary containing all keys
        jwks = get_public_key()

        # python-jose automatically matches the 'kid' (Key ID) in the token
        # to the correct RSA key inside the jwks dictionary!
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={
                "verify_iss": False,
                "verify_aud": False
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
