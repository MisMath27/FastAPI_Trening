from imports import *
import jwt
from datetime import timedelta


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login_6")
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUT = 1
REFRESH_TOKEN_EXPIRE_MINUT = 3
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_jwt_token(data: Dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(username: str) -> str:
    payload = {"sub": username, "type": "access"}
    return create_jwt_token(payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUT))


def create_refresh_token(username: str) -> str:
    payload = {"sub": username, "type": "refresh"}
    return create_jwt_token(payload, timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUT))


def verify_jwt_token(token: str) -> Dict:
    """Проверяет JWT токен."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_user_from_token(token: str = Depends(oauth2_scheme)):
    """Извлекает имя пользователя из JWT токена (для dependencies)"""

    # ===== ДОБАВЛЯЕМ ОЧИСТКУ ТОКЕНА =====
    # Убираем "Bearer " если оно есть
    if token and token.startswith("Bearer "):
        token = token.replace("Bearer ", "")
        print("⚠Убран префикс Bearer")

    print(f"Получен токен: {token[:30]}...")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Токен декодирован: {payload}")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        print("Токен истек")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"Ошибка декодирования: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_refresh_token(token: str) -> Dict:
    payload = verify_jwt_token(token)
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={'WWW-Authenticate': "Bearer"}
        )
    return payload


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)