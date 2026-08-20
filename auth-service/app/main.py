import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.database import engine, Base, get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.security import get_password_hash, verify_password, create_access_token, verify_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("auth-service")

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables strictly on startup if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Authentication Service Database Initialized.")
    yield

app = FastAPI(lifespan=lifespan, title="Auth Service")

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Passwords are NEVER logged or returned in responses
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_pwd)
    
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"New user registered: {new_user.email}")
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")

@app.post("/login", response_model=Token)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalars().first()
    
    if not user or not verify_password(user_in.password, user.hashed_password):
        # Generic error message to prevent enumeration attacks
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    token_data = create_access_token(data={"sub": str(user.id), "email": user.email})
    logger.info(f"User authenticated: {user.email}")
    return token_data

@app.get("/verify")
async def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Protected route used by the API Gateway to validate downstream requests.
    Returns HTTP 200 with the decoded payload if valid, or HTTP 401 if invalid.
    """
    payload = verify_token(credentials.credentials)
    return {"status": "valid", "user_id": payload.get("sub")}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}