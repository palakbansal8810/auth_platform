from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from app.database import get_db
from app.models import User, AuthProvider
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/login")
async def google_login(request: Request):
    redirect_uri = f"{request.base_url}auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token["userinfo"]

        email = userinfo["email"]
        name = userinfo["name"]
        google_id = userinfo["sub"]

        # Find or create user
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)

        # Link Google provider
        provider = db.query(AuthProvider).filter_by(
            provider="google",
            provider_user_id=google_id
        ).first()

        if not provider:
            db.add(AuthProvider(
                user_id=user.id,
                provider="google",
                provider_user_id=google_id
            ))
            db.commit()

        jwt = create_token(user.id)
        return RedirectResponse(f"{FRONTEND_URL}/callback?token={jwt}")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))