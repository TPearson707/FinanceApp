# # Configuration
# SECRET_KEY = "hello" # Remember to replace later
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# # Fake database for testing
# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "full_name": "John Doe",
#         "email": "johndoe@gmail.com",
#         "hashed_password" : "", # bcrypt hash of "secret"
#         "password": "$2y$10$J9qb1SyXhCnAhCpGLFVA8uUs50yeK9X9.X28s6Gb5ZD9kOvewbt7.", 
#         "disabled": False,
#     }
# }

# # Password hasing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # OAuth2 scheme
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# # Pydantic models
# class User(BaseModel):
#     username: str
#     email: str
#     full_name: str
#     disabled: bool = None

# class UserInDB(User):
#     hashed_password: str

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: str | None = None

# # Utility functions
# def get_user(fake_users_db, username: str):
#     print(f"Looking up user: {username}")
#     if username in fake_users_db:
#         user_dict = fake_users_db[username]
#         return UserInDB(**user_dict)

# def verify_password(plain_password, hashed_password):
#     return pwd_context.verify(plain_password, hashed_password)

# def get_password_hash(password):
#     return pwd_context.hash(password)

# def authenticate_user(fake_db, username: str, password: str):
#     user = fake_db.get(username)
#     if not user:
#         return False
#     if not verify_password(password, user['hashed_password']):
#         return False
#     return user

# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.now(datetime.timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(datetime.timezone.utc) + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt

# # FastAPI app
# app = FastAPI()

# # basic route
# @app.get("/")
# async def root():
#     return {"message": "Welcome to my FastAPI app!"}

# # Routes
# @app.post("/token", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = authenticate_user(fake_users_db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     print("is user")
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.get("/users/me", response_model=User)
# async def read_users_me(token: str = Depends(oauth2_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise credentials_exception
#         token_data = TokenData(username=username)
#     except JWTError:
#         raise credentials_exception
#     user = get_user(fake_users_db, username=token_data.username)
#     if user is None:
#         raise credentials_exception
#     return user