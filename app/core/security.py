from jose import jwt, JWTError
from fastapi import HTTPException, Header

from app.core.config import settings

def get_current_user(authorization: str = Header(...)):
    """Validate JWT token from Supabase and return user ID"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Decode and validate JWT using Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        # Extract user ID from sub claim
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        
        return user_id
        
    except JWTError as e:
        print(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        print(f"Unexpected authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")