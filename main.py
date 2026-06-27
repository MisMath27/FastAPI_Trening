from imports import *


# Загружаем конфигурацию
config = load_config()

app = FastAPI()


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
        # ИСПРАВЛЕНО: правильный паттерн с закрывающей скобкой
        pattern = r'\b(' + '|'.join(forbidden) + r')\b'
        # ИСПРАВЛЕНО: re.search вместо re.rearch
        if re.search(pattern, message, re.IGNORECASE):
            raise ValueError("Сообщение содержит запрещенные слова")
        return message


@app.get("/")
def read_root():
    logger.info("Корневой маршрут вызван")
    return {"message": "Здарова, заебал!"}



# class User(BaseModel):
#     name: str
#     age: int

# class UserResponse(BaseModel):
#     message: str
#     user: User
#
# @app.post("/users/", response_model=UserResponse)
# async def create_user(user: User):
#     return {"message": f"Пользователь {user.name} создан!", "user": user}


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
    """Маршрут для проверки конфигурации"""
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
        while chunk := await file.read(1024):  # Читаем по 1 КБ
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

# SECRET_KEY = config.secret_key
# session_manager = SessionManager(SECRET_KEY)
#
# @app.post('/login')
# async def login(
#     response: Response,
#     Log: Log
# ):
#     # Если пришёл JSON через Log
#     if Log:
#         username = Log.name
#         pwd = Log.password
#
#     if not username or not pwd:
#         raise HTTPException(status_code=400, detail="Username and password required")
#
#     if username == "admin" and pwd == "secret":
#         user_id = str(uuid.uuid4())
#         signed_token = signer.sign(user_id).decode('utf-8')
#
#         response.set_cookie(
#             key="session_token",
#             value=signed_token,
#             httponly=True,
#             secure=False,
#             samesite="lax",
#             max_age=3600
#         )
#         return {
#             "message": "Login successful",
#             "session_token": signed_token,
#             "user_id": user_id
#         }
#
#     raise HTTPException(status_code=401, detail="Unauthorized")

# @app.get('/profile')
# async def get_profile(session_token: Optional[str] = Cookie(None)):
#     if not session_token:
#         raise HTTPException(status_code=401, detail="Unauthorized: No session token")
#
#     try:
#         user_id = signer.unsign(session_token).decode('utf-8')
#     except Exception:
#         raise HTTPException(status_code=401, detail="Unauthorized: Invalid signature")
#
#     profile_data = {
#         "user_id": user_id,
#         "username": "admin",
#         "email": "admin@example.com",
#         "role": "user"
#     }
#
#     return {
#         "message": "Profile accessed successfully",
#         "profile": profile_data
#     }


# @app.post('/logout')
# async def logout(response: Response):
#     response.delete_cookie("session_token")
#     return{"message": "Logout successful"}


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

    def validate_and_refresh_token(self, token: str, current_time: Optional[int] = None) -> tuple[bool, Optional[str], Optional[str], Optional[int]]:
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


SECRET_KEY = config.secret_key or "your-secret-key-here-change-in-production"
session_manager = SessionManager(SECRET_KEY)

class LoginData(BaseModel):
    name: str
    password: str


@app.post('/login')
async def login(
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
        raise HTTPException(status_code=status.HTTP_401_UNATHORIZED, detail="Unauthorized: No session token")

    current_time = int(time.time())
    is_valid, should_refresh, user_id, new_timestamp = session_manager.validate_and_refresh_token(session_token, current_time)

    if not is_valid:

        try:
            parts = session_token.split('.')
            if len(parts) == 3:
                timestamp  = int(parts[1])
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
    return{"message": "Logout successful"}



class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias='User-Agent', description='User-Agent user headers')
    accept_language: str = Field(..., alias='Accept-Language', description='Accept-Language user geaders')

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
    """
    Извлекает заголовки из запроса и возвращает модель CommonHeaders
    """
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
            detail="Missing required haider: User-Agent"

        )

    if accept_language is None:
        raise HTTPException(
            status_code=400,
            detail='Missing required haider: Accept-Language'
        )

    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


MINIMUM_APP_VERSION = '0.0.2'


def compare_versions(current: str, minimum: str) -> bool:
    """
    Сравнивает версии.
    Возвращает True, если current >= minimum
    """
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


@app.get('/info')
async def get_info(
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
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    user_found = False
    for user in USER_DATA:
        if user.username == credentials.username and user.password == credentials.password:
            user_found = True
            break

    if not user_found:
        headers = {'WWW-Authenticate': "Basic"}
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect date of username',
            headers=headers
        )

    return {"message": "You got my secret, welcome"}



class AuthUserBase(BaseModel):
    username: str


class AuthUserRegister(AuthUserBase):
    password: str


class AuthUserInDB(AuthUserBase):
    hashed_password: str


def hash_password(password: str) -> str:
    password_bytes = password[:72].encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    password_bytes = password[:72].encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)



fake_users_db: dict[str, AuthUserInDB] = {}


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



@app.post("/register")
async def register(user: AuthUserRegister):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = hash_password(user.password)

    fake_users_db[user.username] = AuthUserInDB(
        username=user.username,
        hashed_password=hashed_password
    )

    return {"message": f"User {user.username} registered successfully"}



@app.get("/login")
async def login(user: AuthUserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=config.debug)