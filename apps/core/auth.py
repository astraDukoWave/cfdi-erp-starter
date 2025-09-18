from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import os

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))

DEMO_USER = os.getenv("DEMO_USER", "admin@example.com")
DEMO_PASS = os.getenv("DEMO_PASS", "pass123")

security = HTTPBearer(auto_error=True)

# Simply: generar una “nota firmada” con expiración.
def create_access_token(sub: str, minutes: int = ACCESS_TOKEN_MINUTES) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

# Simply: revisar y decodificar la “nota firmada”.
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Simply: dependencia de FastAPI que exige un Bearer token válido.
def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    payload = decode_token(creds.credentials)
    return payload.get("sub")

# Simply: login DEMO: valida user/pass contra .env
def verify_demo_credentials(username: str, password: str) -> bool:
    return username == DEMO_USER and password == DEMO_PASS
