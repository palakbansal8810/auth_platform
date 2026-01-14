from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from app.database import get_db
from app.models import User, AuthProvider
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register")
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
 
    user = db.query(User).filter(User.email == data.email).first()
    
    # Check if password login already exists
    if user:
        provider = db.query(AuthProvider).filter_by(
            user_id=user.id,
            provider="local"
        ).first()
        
        if provider:
            # User already has password - tell them to login
            raise HTTPException(
                status_code=400, 
                detail="An account with this email already exists. Please login instead."
            )
        
        # User exists from OAuth - adding password to existing account
        # This is intentional to allow linking accounts
    else:
        # Create brand new user
        user = User(email=data.email, name=data.name)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Add password authentication
    new_provider = AuthProvider(
        user_id=user.id,
        provider="local",
        password_hash=pwd_context.hash(data.password)
    )
    db.add(new_provider)
    db.commit()

    token = create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    
    # Find user
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Find local auth provider
    provider = db.query(AuthProvider).filter_by(
        user_id=user.id,
        provider="local"
    ).first()
    
    if not provider:
        # User exists but has no password (OAuth only)
        raise HTTPException(
            status_code=401, 
            detail="No password set for this account. Try logging in with Google or Okta."
        )
    
    # Verify password
    if not pwd_context.verify(data.password, provider.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Generate and return token
    token = create_token(user.id)
    return {"access_token": token, "token_type": "bearer"}