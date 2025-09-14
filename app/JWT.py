import os
from datetime import datetime,timedelta
from jose import jwt,JWTError

JWT_SECRET = os.getenv("JWT_SECRET","dev-secret")
JWT_ALGO = "HS256"
JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN","60"))

def create_token(e_mail:str,role:str)->str:
    payload = {
        "sub": e_mail,
        "role": role,
        "exp": datetime.utcnow() +timedelta(minutes=JWT_EXPIRES_MIN),
    }
    return jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALGO)

def decode_token(token:str)->dict:
    try:
        return jwt.decode(token,JWT_SECRET,algorithms=[JWT_ALGO])
    except JWTError:
        raise ValueError("invalid token")
