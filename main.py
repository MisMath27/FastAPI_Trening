from security import (
    create_access_token,
    create_refresh_token,
    create_jwt_token,
    verify_refresh_token,
    verify_password,
    hash_password,
    get_user_from_token,
    ACCESS_TOKEN_EXPIRE_MINUT,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from db import *
from models import *
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from models import TokenResponse, RefreshRequest, Users, UserLogin
from rbac import PermissionChecker
from dependencies import get_current_user, get_current_user_model
from security import oauth2_scheme




config = load_config()
logger = logging.getLogger(__name__)

MODE = settings.MODE.upper()
if MODE not in ['DEV', 'PROD']:
    logger.warning(f'Unknown mode: {MODE}. Using dev mode')
    MODE = 'DEV'

if MODE == 'PROD':
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        title="API (PROD)"
    )
    logger.info("Application started in PROD mode - documentation disabled")
else:
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        title="API (DEV)"
    )
    logger.info("Application started in DEV mode - documentation will be protected")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def authenticate_docs(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    if MODE != "DEV":
        raise HTTPException(status_code=404, detail='Not Found')
    correct_username = secrets.compare_digest(
        credentials.username,
        settings.DOCS_USER or 'admin'
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        settings.DOCS_PASSWORD or 'secret'
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': "Basic"},
        )
    return credentials


if MODE == "DEV":
    from fastapi.openapi.docs import get_swagger_ui_html
    from fastapi.openapi.utils import get_openapi


    @app.get('/docs', include_in_schema=False)
    async def custom_swagger_ui_html(auth: HTTPBasicCredentials = Depends(authenticate_docs)):
        return get_swagger_ui_html(
            openapi_url='/openapi.json',
            title='API Documentation',
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )


    @app.get('/openapi.json', include_in_schema=False)
    async def custom_openapi_json(
            auth: HTTPBasicCredentials = Depends(authenticate_docs)
    ):
        return app.openapi()


    logger.info("Docs available at /docs with basic auth")


class Contact(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=7, max_length=15)

    @validator('phone')
    def validate_phone(cls, phone):
        if phone is not None:
            if not re.match(r'^\d{7,15}$', phone):
                raise ValueError('Invalid phone number')
        return phone


class Feedback(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=10, max_length=500)
    contact: Contact

    @validator('message')
    def validate_message(cls, message):
        forbidden = ["редиска", "бяка", "козявка"]
        pattern = r'\b(' + '|'.join(forbidden) + r')\b'
        if re.search(pattern, message, re.IGNORECASE):
            raise ValueError("Сообщение содержит запрещенные слова")
        return message


@app.get("/")
def read_root():
    logger.info("Корневой маршрут вызван")
    return {"message": "Здарова, заебал!"}


class Event(BaseModel):
    name: str
    timestamp: datetime


@app.post("/events/")
async def create_event(event: Event):
    return event


@app.get("/custom")
def read_custom_message():
    logger.info("Маршрут /custom вызван")
    return {"message": "This is a custom message!"}


@app.get("/config")
def get_config():
    return {
        "secret_key": config.secret_key,
        "database_url": config.db.database_url,
        "debug": config.debug,
    }


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    with open(file.filename, "wb") as f:
        while chunk := await file.read(1024):
            f.write(chunk)
    return {"filename": file.filename}


@app.post("/multiple-files/")
async def upload_multiple_files(files: List[UploadFile]):
    return {"filenames": [file.filename for file in files]}


@app.get("/hello/{name}")
def hello(name: str):
    logger.info(f"Приветствие для {name}")
    return {"message": f"Привет, {name}!"}


@app.post('/feedback')
async def create_feedback(feedback: Feedback, is_premium: bool = Query(False)):
    response_message = f'Спасибо, {feedback.name}! Ваш отзыв сохранён.'
    if is_premium:
        response_message += " Ваш отзыв будет рассмотрен в приоритетном порядке."
    return {'message': response_message}


@app.get("/items/")
async def read_item(
        skip: int = Query(0, alias="start", ge=0),
        limit: int = Query(10, le=100)
):
    return {"skip": skip, "limit": limit}


class UserCreate(BaseModel):
    name: str
    email: str
    age: int
    is_subscribed: bool


@app.post("/create_user/")
async def create_item(create_user: UserCreate):
    return create_user


sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99}
]


@app.get('/product/{product_id}')
async def get_product(product_id: int):
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.get('/products/search')
async def search_products(
        keyword: str,
        category: Optional[str] = None,
        limit: int = Query(10, ge=1, le=100)
):
    res = []
    keyword = keyword.lower()
    for product in sample_products:
        if keyword not in product['name'].lower():
            continue
        if category and product['category'].lower() != category.lower():
            continue
        res.append(product)
        if len(res) >= limit:
            break
    return res


class Log(BaseModel):
    name: str
    password: str


class SessionManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode('utf-8')
        self.session_lifetime = 300
        self.refresh_threshold = 180

    def _create_signature(self, user_id: str, timestamp: int) -> str:
        message = f"{user_id}.{timestamp}".encode('utf-8')
        signature = hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()
        return signature

    def _verify_signature(self, user_id: str, timestamp: int, signature: str) -> bool:
        expected_signature = self._create_signature(user_id, timestamp)
        return hmac.compare_digest(expected_signature, signature)

    def create_session_token(self, user_id: str) -> str:
        timestamp = int(time.time())
        signature = self._create_signature(user_id, timestamp)
        return f"{user_id}.{timestamp}.{signature}"

    def validate_and_refresh_token(self, token: str, current_time: Optional[int] = None) -> tuple[
        bool, Optional[str], Optional[str], Optional[int]]:
        if current_time is None:
            current_time = int(time.time())
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return False, False, None, None
            user_id = parts[0]
            timestamp_str = parts[1]
            provided_signature = parts[2]
            try:
                timestamp = int(timestamp_str)
            except ValueError:
                return False, False, None, None
        except Exception:
            return False, False, None, None
        if not self._verify_signature(user_id, timestamp, provided_signature):
            return False, False, None, None
        time_since_activity = current_time - timestamp
        if time_since_activity > self.session_lifetime:
            return False, False, None, None
        should_refresh = time_since_activity >= self.refresh_threshold
        new_timestamp = current_time if should_refresh else None
        return True, should_refresh, user_id, new_timestamp

    def create_refreshed_token(self, user_id: str, timestamp: int) -> str:
        signature = self._create_signature(user_id, timestamp)
        return f"{user_id}.{timestamp}.{signature}"


SECRET_KEY = "your-secret-key-here-change-in-production"
session_manager = SessionManager(SECRET_KEY)


class LoginData(BaseModel):
    name: str
    password: str


@app.post('/login_session')
async def login_session(
        response: Response,
        login_data: LoginData
):
    username = login_data.name
    pwd = login_data.password
    if not username or not pwd:
        raise HTTPException(status_code=400, detail="Username and password required")
    if username == "admin" and pwd == "secret":
        user_id = str(uuid.uuid4())
        session_token = session_manager.create_session_token(user_id)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=300
        )
        return {
            "message": "Login successful",
            "session_token": session_token,
            "user_id": user_id,
            "expires_in": 300
        }
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.get('/profile')
async def get_profile(response: Response, request: Request, session_token: Optional[str] = Cookie(None)):
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized: No session token")
    current_time = int(time.time())
    is_valid, should_refresh, user_id, new_timestamp = session_manager.validate_and_refresh_token(session_token,
                                                                                                  current_time)
    if not is_valid:
        try:
            parts = session_token.split('.')
            if len(parts) == 3:
                timestamp = int(parts[1])
                if current_time - timestamp > session_manager.session_lifetime:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    if should_refresh and new_timestamp is not None:
        new_token = session_manager.create_refreshed_token(user_id, new_timestamp)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=300
        )
        logger.info(f"Session refreshed for user {user_id} at timestamp {new_timestamp}")
    profile_data = {
        "user_id": user_id,
        "username": "admin",
        "email": "admin@example.com",
        "role": "user",
        "session_updated": should_refresh,
        "current_time": current_time
    }
    return {
        "message": "Profile accessed successfully",
        "profile": profile_data
    }


@app.post('/logout')
async def logout(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Logout successful"}


class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias='User-Agent', description='User-Agent user headers')
    accept_language: str = Field(..., alias='Accept-Language', description='Accept-Language user headers')

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

    @validator('accept_language')
    def validate_accept_language(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Invalid Accept-Language format: empty or too short")
        parts = v.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                raise ValueError("Invalid Accept-Language format: empty part")
            if ';' in part:
                lang_part, quality_part = part.split(';', 1)
                lang_part = lang_part.strip()
                quality_part = quality_part.strip()
                if not quality_part.startswith('q='):
                    raise ValueError("Invalid Accept-Language format: invalid quality parameter format")
                try:
                    q_value = float(quality_part[2:])
                    if not (0 <= q_value <= 1):
                        raise ValueError("Invalid Accept-Language format: quality value must be between 0 and 1")
                except ValueError:
                    raise ValueError("Invalid Accept-Language format: invalid quality value")
            else:
                lang_part = part.strip()
            if not lang_part:
                raise ValueError("Invalid Accept-Language format: empty language tag")
            if not re.match(r'^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$', lang_part):
                raise ValueError(f'Invalid Accept-Language format: invalid language tag "{lang_part}"')
        return v


async def get_common_headers(
        user_agent: str = Header(..., alias="User-Agent"),
        accept_language: str = Header(..., alias="Accept-Language")
) -> CommonHeaders:
    return CommonHeaders(
        user_agent=user_agent,
        accept_language=accept_language
    )


@app.get('/headers')
async def get_headers_common(headers: CommonHeaders = Depends(get_common_headers)):
    return headers.model_dump(by_alias=True)


@app.get('/info')
async def get_info(response: Response = None, headers: CommonHeaders = Depends(get_common_headers)):
    server_time = datetime.now().isoformat()
    if response:
        response.headers["X-Server-Time"] = server_time
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": headers.dict(by_alias=True),
        "server_time": server_time
    }


@app.get('/headers_2')
async def det_headers(request: Request,
                      user_agent: Optional[str] = Header(None, alias="User-Agent"),
                      accept_language: Optional[str] = Header(None, alias='Accept-Language')):
    if user_agent is None:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: User-Agent"
        )
    if accept_language is None:
        raise HTTPException(
            status_code=400,
            detail='Missing required header: Accept-Language'
        )
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


MINIMUM_APP_VERSION = '0.0.2'


def compare_versions(current: str, minimum: str) -> bool:
    try:
        return version.parse(current) >= version.parse(minimum)
    except Exception:
        return False


class CommonHeaders_2(BaseModel):
    user_agent: str = Field(
        ...,
        alias='User-Agent',
        description='User-Agent header'
    )
    accept_language: str = Field(
        ...,
        alias='Accept-Language',
        description='Accept-Language header'
    )
    x_current_version: str = Field(
        ...,
        alias='X-Current-Version',
        description='Current app version (format: X.Y.Z)'
    )

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True

    @validator('accept_language')
    def validate_accept_language(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Invalid Accept-Language format: empty or too short")
        parts = v.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                raise ValueError("Invalid Accept-Language format: empty part")
            if ';' in part:
                lang_part, quality_part = part.split(';', 1)
                lang_part = lang_part.strip()
                quality_part = quality_part.strip()
                if not quality_part.startswith('q='):
                    raise ValueError("Invalid Accept-Language format: invalid quality parameter format")
                try:
                    q_value = float(quality_part[2:])
                    if not (0 <= q_value <= 1):
                        raise ValueError("Invalid Accept-Language format: quality value must be between 0 and 1")
                except ValueError:
                    raise ValueError("Invalid Accept-Language format: invalid quality value")
            else:
                lang_part = part.strip()
            if not lang_part:
                raise ValueError("Invalid Accept-Language format: empty language tag")
            if not re.match(r'^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$', lang_part):
                raise ValueError(f'Invalid Accept-Language format: invalid language tag "{lang_part}"')
        return v

    @validator('x_current_version')
    def validate_version(cls, v: str) -> str:
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError(f'Invalid version format: "{v}". Expected format: X.Y.Z (e.g., 1.2.3)')
        if not compare_versions(v, MINIMUM_APP_VERSION):
            raise ValueError(
                f'Требуется обновить приложение. '
                f'Ваша версия: {v}, минимальная: {MINIMUM_APP_VERSION}'
            )
        return v


async def get_common_headers_2(
        user_agent: str = Header(..., alias="User-Agent"),
        accept_language: str = Header(..., alias="Accept-Language"),
        x_current_version: str = Header(..., alias="X-Current-Version")
) -> CommonHeaders_2:
    return CommonHeaders_2(
        user_agent=user_agent,
        accept_language=accept_language,
        x_current_version=x_current_version
    )


@app.get('/headers_3')
async def get_headers_common(headers: CommonHeaders_2 = Depends(get_common_headers_2)):
    return headers.dict(by_alias=True)


@app.get('/info_2')
async def get_info_2(
        response: Response,
        headers: CommonHeaders_2 = Depends(get_common_headers_2)
):
    server_time = datetime.now().isoformat()
    response.headers["X-Server-Time"] = server_time
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": headers.dict(by_alias=True),
        "server_time": server_time
    }


security = HTTPBasic()


class User(BaseModel):
    username: str
    password: str


USER_DATA = [
    User(**{"username": "user1", "password": "pass1"}),
    User(**{"username": "user2", "password": "pass2"})
]


@app.get('/login_2')
async def login_basic(credentials: HTTPBasicCredentials = Depends(security)):
    user_found = False
    for user in USER_DATA:
        if user.username == credentials.username and user.password == credentials.password:
            user_found = True
            break
    if not user_found:
        headers = {'WWW-Authenticate': "Basic"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers=headers
        )
    return {"message": "You got my secret, welcome"}


class AuthUserBase(BaseModel):
    username: str


class AuthUserRegister(AuthUserBase):
    password: str


class AuthUserInDB(AuthUserBase):
    hashed_password: str
    roles: list = []


def hash_password(password: str) -> str:
    password_bytes = password[:72].encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    password_bytes = password[:72].encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


fake_users_db: dict[str, AuthUserInDB] = {}
refresh_tokens_store: dict[str, str] = {}


def auth_user(credentials: HTTPBasicCredentials = Depends(security)) -> AuthUserInDB:
    username = credentials.username
    user = fake_users_db.get(username)
    if user is None:
        fake_password = credentials.password[:72]
        fake_hashed = hash_password("fake")
        verify_password(fake_password, fake_hashed)
        headers = {'WWW-Authenticate': "Basic"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers=headers
        )
    if not verify_password(credentials.password, user.hashed_password):
        headers = {'WWW-Authenticate': "Basic"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers=headers
        )
    if not secrets.compare_digest(username, user.username):
        headers = {"WWW-Authenticate": "Basic"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers=headers
        )
    return user


@app.post("/register_old")
async def register_old(user: AuthUserRegister):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = hash_password(user.password)
    fake_users_db[user.username] = AuthUserInDB(
        username=user.username,
        hashed_password=hashed_password
    )
    return {"message": f"User {user.username} registered successfully"}


@app.get("/login_3")
async def login_bcrypt(user: AuthUserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}


@app.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def register_new(request: Request, user_data: AuthUserRegister):
    logger.info(f"Registration: {user_data.username}")
    for existing_username in fake_users_db:
        if secrets.compare_digest(existing_username, user_data.username):
            logger.warning(f"User {user_data.username} already exists")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )
    hashed_password = hash_password(user_data.password)
    fake_users_db[user_data.username] = AuthUserInDB(
        username=user_data.username,
        hashed_password=hashed_password
    )
    logger.info(f"User {user_data.username} created")
    return {"message": "New user created"}


@app.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """
    Аутентификация пользователя.
    Возвращает access_token и refresh_token.

    Ограничение: 5 запросов в минуту
    """
    logger.info(f"Login: {login_data.username}")

    user = None
    for stored_username in fake_users_db:
        if secrets.compare_digest(stored_username, login_data.username):
            user = fake_users_db[stored_username]
            break

    if user is None:
        logger.warning(f"User {login_data.username} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Invalid password for {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )

    access_token = create_access_token(login_data.username)
    refresh_token = create_refresh_token(login_data.username)

    safe_refresh_token(login_data.username, refresh_token)

    logger.info(f"Tokens created for {login_data.username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


class RefreshRequest(BaseModel):
    refresh_token: str


@app.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh_tokens(request: Request, refresh_data: RefreshRequest):
    """
    Обновление токенов с использованием refresh-токена.

    Шаги:
    1. Проверяем refresh-токен
    2. Проверяем, что он сохранён в хранилище
    3. Удаляем старый токен
    4. Создаём новую пару токенов
    5. Сохраняем новый refresh-токен

    Ограничение: 5 запросов в минуту
    """
    logger.info("Refresh tokens request")

    refresh_token = refresh_data.refresh_token

    try:
        payload = verify_refresh_token(refresh_token)
        username = payload.get("sub")
    except HTTPException as e:
        logger.warning(f"Invalid refresh token: {e.detail}")
        raise e

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    if not validate_refresh_token(username, refresh_token):
        logger.warning(f"Refresh token not found for {username}")
        delete_refresh_token(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or already used"
        )

    delete_refresh_token(username)

    new_access_token = create_access_token(username)
    new_refresh_token = create_refresh_token(username)

    safe_refresh_token(username, new_refresh_token)

    logger.info(f"Tokens refreshed for {username}")

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@app.post("/login_4", response_model=TokenResponses)
async def login_4(login_data: LoginRequest):
    print(f"Получен запрос на /login_4")
    print(f"Username: {login_data.username}")
    print(f"Password: {login_data.password}")

    user = None
    for stored_username in fake_users_db:
        if secrets.compare_digest(stored_username, login_data.username):
            user = fake_users_db[stored_username]
            break

    if user is None:
        print("Ошибка: Пользователь не найден")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not verify_password(login_data.password, user.hashed_password):
        print("Ошибка: Неверный пароль")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

    print("Создание JWT токена...")
    access_token = create_access_token(login_data.username)
    print(f"Токен создан: {access_token[:50]}...")

    return {
        "access_token": access_token,
        "refresh_token": create_refresh_token(login_data.username),
        "token_type": "bearer"
    }


@app.get("/protected_resource")
async def protected_resource(current_user: str = Depends(get_current_user)):
    """
    Защищённый маршрут.
    Доступен только с валидным access-токеном.
    """
    return {
        "message": "Access grant to protected resource",
        "user": current_user,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/about_me")
async def about_me(current_user: str = Depends(get_current_user)):
    user = None
    for u in USER_DATA:
        if u.get("username") == current_user:
            user = u
            break
    if user:
        return {
            "username": user["username"],
            "message": f'Welcome, {current_user}!'
        }
    return {"error": "User not found"}


@app.get("/debug/tokens")
async def debug_tokens():
    """
    Отладочный маршрут для просмотра хранилища refresh-токенов.
    """
    return {
        "refresh_tokens_store": refresh_tokens_store,
        "users": list(fake_users_db.keys())
    }


@app.get("/debug/time")
async def debug_time():
    """
    Показывает текущее время сервера для проверки истечения токенов.
    """
    from security import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUT
    return {
        "current_time": datetime.now().isoformat(),  # ← убрать datetime.
        "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_minutes": REFRESH_TOKEN_EXPIRE_MINUT
    }


@app.post("/login_6", response_model=TokenResponse)
async def login_6(user_in: UserLogin):
    """Маршрут для аутентификации с ролью"""
    user = get_user(user_in.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if user.get("password") != user_in.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_data = {
        "sub": user_in.username,
        "roles": user.get("roles", ["user"])
    }
    token = create_jwt_token(token_data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUT))
    return {"access_token": token, "token_type": "bearer"}


@app.get("/guest_only", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["guest", "user", "admin"])
@limiter.limit("5/minute")
async def guest_only(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": f"Welcome, {current_user.get('username')}! You have read-only access.",
        "user": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "permissions": ["read"]
    }

@app.get("/user_only", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["user", "admin"])
@limiter.limit("20/minute")
async def user_info(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": f"Welcome, {current_user.get('username')}! You have user access.",
        "user": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "permissions": ["read", "update"]
    }

@app.get("/admin_only", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["admin"])
@limiter.limit("1000/minute")
async def admin_info(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "Welcome, Admin! You have full access.",
        "user": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "permissions": ["create", "read", "update", "delete"]
    }


@app.get("/my_profile", dependencies=[Depends(oauth2_scheme)])
async def my_profile(current_user: dict = Depends(get_current_user)):
    """Показывает профиль текущего пользователя"""
    return {
        "username": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "full_name": current_user.get("full_name"),
        "email": current_user.get("email"),
        "disabled": current_user.get("disabled", False)
    }


@app.post("/admin/create_resource", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["admin"])
async def create_resource(
    resource_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Создание ресурса (только для администраторов)"""
    return {
        "message": "Resource created successfully",
        "created_by": current_user.get("username"),
        "resource": resource_data
    }


@app.put("/user/update_resource/{resource_id}", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["user", "admin"])
async def update_resource(
    resource_id: int,
    resource_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Обновление ресурса (для пользователей и администраторов)"""
    return {
        "message": f"Resource {resource_id} updated successfully",
        "updated_by": current_user.get("username"),
        "resource": resource_data
    }


@app.delete("/admin/delete_resource/{resource_id}", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["admin"])
async def delete_resource(
    resource_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Удаление ресурса (только для администраторов)"""
    return {
        "message": f"Resource {resource_id} deleted successfully",
        "deleted_by": current_user.get("username")
    }


@app.get("/guest/read_resource/{resource_id}", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["guest", "user", "admin"])
async def read_resource(
    resource_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Чтение ресурса (для всех ролей)"""
    return {
        "message": f"Resource {resource_id} read successfully",
        "read_by": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "resource": {
            "id": resource_id,
            "name": f"Sample Resource {resource_id}",
            "description": "This is a read-only resource for all roles"
        }
    }


@app.get("/protected_resource_rbac", dependencies=[Depends(oauth2_scheme)])
@PermissionChecker(["admin", "user"])
async def protected_resource_rbac(current_user: dict = Depends(get_current_user)):
    """Защищённый маршрут. Доступен только admin и user."""
    return {
        "message": "Access granted to protected resource",
        "user": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/debug/roles", dependencies=[Depends(oauth2_scheme)])
async def debug_roles():
    """Отладочный маршрут для просмотра всех пользователей и их ролей"""
    users_with_roles = []
    for user in USERS_DATA:
        users_with_roles.append({
            "username": user.get("username"),
            "roles": user.get("roles", []),
            "full_name": user.get("full_name"),
            "email": user.get("email")
        })
    return {
        "users": users_with_roles,
        "total_users": len(users_with_roles)
    }


@app.post("/assign_role/{username}")
async def assign_role_to_user(
        username: str,
        role: str
):
    """
    Назначает роль существующему пользователю.
    Временный эндпоинт для тестирования.
    """
    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = fake_users_db[username]

    if not hasattr(user, 'roles'):
        user.roles = []

    if role not in user.roles:
        user.roles.append(role)

    return {
        "message": f"Role '{role}' assigned to user '{username}'",
        "username": username,
        "roles": user.roles
    }


@app.get("/debug/me")
async def debug_me(current_user: dict = Depends(get_current_user)):
    """
    Показывает информацию о текущем пользователе.
    Полезно для отладки.
    """
    return {
        "username": current_user.get("username"),
        "roles": current_user.get("roles", []),
        "has_roles": "roles" in current_user,
        "full_user_data": current_user
    }


@app.get("/debug/db")
async def debug_db():
    """Показывает содержимое fake_users_db"""
    users = {}
    for username, user in fake_users_db.items():
        users[username] = {
            "username": user.username,
            "hashed_password": user.hashed_password[:20] + "...",
            "roles": getattr(user, 'roles', [])
        }
    return {
        "users": users,
        "total": len(fake_users_db)
    }




if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=config.debug)