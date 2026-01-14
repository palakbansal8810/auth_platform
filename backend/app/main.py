from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.auth import google, okta, local
from app.users import router as users_router
from starlette.middleware.sessions import SessionMiddleware
import os
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Platform API",swagger="2.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"),
    max_age=3600,  
    same_site="lax",
    https_only=False  
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google.router, prefix="/auth/google", tags=["Google Auth"])
app.include_router(okta.router, prefix="/auth/okta", tags=["Okta SAML"])
app.include_router(local.router, prefix="/auth/local", tags=["Local Auth"])
app.include_router(users_router, prefix="/api", tags=["Users"])

@app.get("/")
async def root():
    return {"message": "Auth Platform API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}    