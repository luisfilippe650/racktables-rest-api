from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
# Ensure ACCESS_TOKEN_EXPIRE_MINUTES is an int (fixes TypeError when it's read as string)
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 15

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/racktables/login")


# criando o token
def create_access_token(data: dict) -> str:

    payload = data.copy()

    # Fix claim mismatch: prefer 'sub' as the subject claim. Accept 'user_id' as input for backward compatibility.
    user = data.get("user_id") or data.get("sub")
    if user is not None:
        payload["sub"] = str(user)
        # remove user_id to avoid duplication inside token
        payload.pop("user_id", None)

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Use integer timestamps for exp/iat for broad compatibility
    payload.update({"exp": int(expire.timestamp()), "iat": int(now.timestamp())})

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return token


# verificador de rotas
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # tolerate both sub and user_id if present
        user_id: str = payload.get("sub") or payload.get("user_id")

        # verificar se o token é valido
        if user_id is None:
            raise credentials_exception

        return user_id

    except ExpiredSignatureError:
        # Explicit handling for expired tokens so clients can react differently (e.g. ask for refresh)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception
