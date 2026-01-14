from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, AuthProvider
from jose import jwt
from datetime import datetime, timedelta
import os
import base64
import urllib.parse
from xml.etree import ElementTree as ET
import uuid

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
OKTA_SSO_URL = os.getenv("OKTA_SSO_URL", "")
OKTA_ISSUER = os.getenv("OKTA_ISSUER", "http://localhost:8000")

def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/login")
async def okta_login(request: Request):
    if not OKTA_SSO_URL:
        raise HTTPException(
            status_code=501,
            detail="Okta not configured. Please set OKTA_SSO_URL in .env file"
        )
    
    # Generate unique request ID
    request_id = f"_request_{uuid.uuid4()}"
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Get the callback URL
    callback_url = f"{OKTA_ISSUER}/auth/okta/callback"
    
    # Create proper SAML AuthnRequest
    saml_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{request_id}"
                    Version="2.0"
                    IssueInstant="{timestamp}"
                    Destination="{OKTA_SSO_URL}"
                    AssertionConsumerServiceURL="{callback_url}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{OKTA_ISSUER}</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress" 
                        AllowCreate="true"/>
</samlp:AuthnRequest>"""
    
    # Encode the SAML request
    encoded = base64.b64encode(saml_request.encode('utf-8')).decode('utf-8')
    
    # URL encode for GET parameter
    encoded_url = urllib.parse.quote(encoded)
    
    # Redirect to Okta with SAML request
    redirect_url = f"{OKTA_SSO_URL}?SAMLRequest={encoded_url}"
    
    return RedirectResponse(redirect_url)

def process_saml_response(saml_response: str, db: Session):
    """Process SAML response and return user"""
    try:
        # Decode the SAML response
        decoded = base64.b64decode(saml_response)
        root = ET.fromstring(decoded)
        
        # Define namespaces
        ns = {
            'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
            'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol'
        }
        
        email = None
        name = None
        
        email_elem = root.find('.//saml:Attribute[@Name="email"]//saml:AttributeValue', ns)
        if email_elem is not None:
            email = email_elem.text
        
        if not email:
            nameid_elem = root.find('.//saml:NameID', ns)
            if nameid_elem is not None:
                email = nameid_elem.text
        
        if not email:
            subject_elem = root.find('.//saml:Subject//saml:NameID', ns)
            if subject_elem is not None:
                email = subject_elem.text
        
        # Try to find name
        name_elem = root.find('.//saml:Attribute[@Name="name"]//saml:AttributeValue', ns)
        if name_elem is not None:
            name = name_elem.text
        
        # Try firstName and lastName
        if not name:
            first_elem = root.find('.//saml:Attribute[@Name="firstName"]//saml:AttributeValue', ns)
            last_elem = root.find('.//saml:Attribute[@Name="lastName"]//saml:AttributeValue', ns)
            if first_elem is not None and last_elem is not None:
                name = f"{first_elem.text} {last_elem.text}"
            elif first_elem is not None:
                name = first_elem.text
        
        if not email:
            print("SAML Response XML:")
            print(ET.tostring(root, encoding='unicode'))
            raise HTTPException(status_code=400, detail="Email not found in SAML response")
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(email=email, name=name or email.split("@")[0])
            db.add(user)
            db.commit()
            db.refresh(user)

        provider = db.query(AuthProvider).filter_by(
            user_id=user.id,
            provider="okta",
            provider_user_id=email
        ).first()

        if not provider:
            db.add(AuthProvider(
                user_id=user.id,
                provider="okta",
                provider_user_id=email
            ))
            db.commit()
        return user
        
    except Exception as e:
        print(f"Okta SAML error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

@router.post("/callback")
async def okta_callback_post(SAMLResponse: str = Form(...), db: Session = Depends(get_db)):
    """Handle POST callback from Okta"""
    try:
        user = process_saml_response(SAMLResponse, db)
        
        # Create JWT token
        access_token = create_token(user.id)
        return RedirectResponse(f"{FRONTEND_URL}/callback?token={access_token}", status_code=303)
    
    except Exception as e:
        print(f"Okta POST callback error: {str(e)}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=okta_auth_failed", status_code=303)

@router.get("/callback")
async def okta_callback_get(SAMLResponse: str = None, db: Session = Depends(get_db)):
    """Handle GET callback from Okta (if configured for HTTP-Redirect)"""
    if not SAMLResponse:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=no_saml_response")
    
    try:
        user = process_saml_response(SAMLResponse, db)
        
        # Create JWT token
        access_token = create_token(user.id)
        return RedirectResponse(f"{FRONTEND_URL}/callback?token={access_token}")
    
    except Exception as e:
        print(f"Okta GET callback error: {str(e)}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=okta_auth_failed")