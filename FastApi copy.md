FastAPI является мощным и быстрым веб-фреймворком для Python, который можно использовать для создания продвинутых приложений. В этом примере мы рассмотрим создание сложного проекта с использованием FastAPI, который включает следующие компоненты:

1. Структура проекта.
2. Модели данных.
3. Роутинг и обработка запросов.
4. Аутентификация и авторизация.
5. Валидация данных и документация.
6. Асинхронные задачи.
7. Тестирование.

### Шаг 1: Установка необходимых библиотек

```bash
pip install fastapi[all] uvicorn sqlalchemy databases alembic pydantic passlib python-jose
```

### Шаг 2: Структура проекта

Создайте структуру проекта, как показано ниже:

```
my_fastapi_app/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── dependencies.py
│   ├── auth.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── api_v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── items.py
│   │   │   │   └── users.py
│   └── core/
│       ├── __init__.py
│       ├── config.py
│       ├── security.py
│
├── alembic/
│
├── alembic.ini
│
├── requirements.txt
│
├── run.py
│
└── README.md
```

### Шаг 3: Настройка конфигурации

**app/core/config.py**

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "mysecretkey"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"

settings = Settings()
```

### Шаг 4: Настройка моделей данных

**app/models.py**

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="items")
```

### Шаг 5: Создание схем данных

**app/schemas.py**

```python
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True
```

### Шаг 6: CRUD операции

**app/crud.py**

```python
from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()

def create_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

### Шаг 7: Настройка аутентификации

**app/auth.py**

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import models, schemas, crud
from .core.config import settings
from .dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = crud.get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Шаг 8: Создание API маршрутов

**app/api/api_v1/endpoints/users.py**

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.dependencies import get_db
from app.auth import get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/me", response_model=schemas.User)
def read_user_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
```

**app/api/api_v1/endpoints/items.py**

```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.dependencies import get_db

### Реализация регистрации и аутентификации в FastAPI

Для реализации регистрации и аутентификации в FastAPI, нам потребуется настроить несколько компонентов, таких как модели данных, схемы данных, обработчики маршрутов и функции для аутентификации. В этом примере мы будем использовать JWT (JSON Web Token) для аутентификации.

### Шаг 1: Установка зависимостей

```bash
pip install fastapi uvicorn sqlalchemy databases pydantic passlib python-jose
```

### Шаг 2: Настройка конфигурации

Создайте файл конфигурации для хранения настроек приложения.

**app/core/config.py**

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "mysecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"

settings = Settings()
```

### Шаг 3: Создание моделей данных

**app/models.py**

```python
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
```

### Шаг 4: Создание схем данных

**app/schemas.py**

```python
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
```

### Шаг 5: CRUD операции

**app/crud.py**

```python
from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

### Шаг 6: Аутентификация

**app/auth.py**

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import models, schemas, crud
from .core.config import settings
from .dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, email: str, password: str):
    user = crud.get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

### Шаг 7: Создание API маршрутов

**app/api/api_v1/endpoints/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import schemas, crud
from app.auth import authenticate_user, create_access_token
from app.dependencies import get_db

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
```

**app/main.py**

```python
from fastapi import FastAPI
from app.api.api_v1.endpoints import auth
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
```

### Шаг 8: Настройка зависимостей

**app/dependencies.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Запуск приложения

**run.py**

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

Этот пример демонстрирует, как настроить базовое приложение FastAPI с регистрацией пользователей и аутентификацией с использованием JWT. Для запуска приложения используйте команду:

```bash
python run.py
```

Теперь ваше приложение доступно по адресу `http://127.0.0.1:8000`. Вы можете протестировать регистрацию и вход в систему с помощью инструментов, таких как Postman или встроенной документации Swagger по адресу `http://127.0.0.1:8000/docs`.

FastAPI автоматически генерирует документацию для API в формате Swagger (OpenAPI). Это одна из самых привлекательных функций FastAPI, так как она упрощает тестирование и документирование вашего API.

Вот как вы можете настроить и использовать Swagger в FastAPI:

### Шаги для создания API с документацией Swagger

### Шаг 1: Установка FastAPI и Uvicorn

Установите FastAPI и Uvicorn с помощью pip:

```bash
pip install fastapi uvicorn
```

### Шаг 2: Создание FastAPI-приложения

Создайте структуру проекта и необходимые файлы.

**project_structure:**
```
fastapi_app/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
└── run.py
```

**app/__init__.py:**

Этот файл может быть пустым или содержать базовые настройки для вашего приложения.

**app/main.py:**

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

### Шаг 3: Запуск FastAPI-приложения с Uvicorn

**run.py:**

```python
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Запустите приложение с помощью команды:

```bash
python run.py
```

### Шаг 4: Доступ к документации Swagger

Когда ваше приложение запущено, вы можете получить доступ к документации Swagger, перейдя по адресу:

```
http://127.0.0.1:8000/docs
```

### Шаг 5: Доступ к документации ReDoc

FastAPI также предоставляет документацию в формате ReDoc. Вы можете получить доступ к ней, перейдя по адресу:

```
http://127.0.0.1:8000/redoc
```

### Пример более сложного API

**app/main.py:**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    return item

@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    fake_item_db = {
        1: {"name": "Foo", "price": 50.5},
        2: {"name": "Bar", "description": "The bartenders", "price": 62.0, "tax": 20.2},
    }
    if item_id not in fake_item_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return fake_item_db[item_id]
```

Этот пример показывает, как создать и получить элементы, используя модели данных и обработчики маршрутов с валидацией данных.

### Резюме

FastAPI предоставляет встроенную поддержку Swagger (OpenAPI), что делает его отличным выбором для разработки и документирования API. Документация создается автоматически, и вы можете легко тестировать свои конечные точки через интерфейсы `/docs` и `/redoc`.