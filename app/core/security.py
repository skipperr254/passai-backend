import requests
from jose import jwt
from jose.backends.rsa_backend import RSAKey
from fastapi import Depends, HTTPException, Header

from app.core.config import settings

JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/jwks"

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header.")
    token = authorization.replace("Bearer ", "")

    # Fetch JWKS (cached later for performance in production)
    jwks = requests.get(JWKS_URL).json()

    # Validate JWT
    try:
        claims = jwt.get_unverified_claims(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token claims.")
    
    # Get the kid from the token header
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    # Find the corresponding public key
    key = None
    for k in jwks["keys"]:
        if k["kid"] == kid:
            key = RSAKey(k, algorithm='RS256')
            break
    
    if not key:
        raise HTTPException(status_code=401, detail="Key not found.")
    
    try:
        payload = jwt.decode(token, key=key, algorithms=["RS256"], audience="authenticated")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload["sub"]  # user_id (correct claim)