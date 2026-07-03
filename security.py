from imports import *
import jwt as pyjwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login_4")

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ACCESS_TOKEN_EXPIRE_MINUT = 1
REFRESH_TOKEN_EXPIRE_MINUT = 3


def create_jwt_token(data: Dict, expires_delta: timedelta) -> str:
    """Создаёт JWT токен с указанным временем жизни."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "type": "access"
    }
    return create_jwt_token(payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUT))


def create_refresh_token(username: str) -> str:
    payload = {
        "sub": username,
        "type": "refresh"
    }
    return create_jwt_token(payload, timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUT))


def verify_jwt_token(token: str) -> Dict:
    """
    Функция для извлечения информации о пользователе из токена. Проверяем токен и извлекаем утверждение о пользователе.
    """
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # Декодируем токен с помощью секретного ключа
        return payload  # Возвращаем утверждение о пользователе (subject) из полезной нагрузки
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_jwt_token_with_expiry(data: Dict, expires_delta: timedelta) -> str:
    """
    Создаёт JWT токен с указанным временем жизни.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_jwt_token(token)
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return username


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


oauth3_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

