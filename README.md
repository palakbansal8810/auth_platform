# Auth Platform – Multi-Provider Authentication System

This project implements a secure authentication platform supporting:

- Email & Password login
- Google OAuth 2.0
- Okta SAML 2.0

The system is deployed on AWS EC2 using Docker, PostgreSQL, Nginx and HTTPS.

---

## 🌐 Live Deployment

**URL:**  
https://assignment.xequaltodata.com

All traffic is forced over HTTPS.

---

## 🧱 Tech Stack

- Backend: FastAPI (Python)
- Frontend: React
- Database: PostgreSQL
- Auth: Google OAuth, Okta SAML, Local Password
- Infrastructure: Docker, Nginx, AWS EC2
- Security: JWT, HTTPS (Let’s Encrypt)

---

## 🧪 Authentication Methods

Users can sign in using:
- Email & Password
- Google account
- Okta SAML

All methods map to the same internal user using email.

---

## 🚀 Run Locally

### 1. Create `.env`
DATABASE_URL=postgresql://postgres:postgres@db:5432/authdb
SECRET_KEY=your_secret_key
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
OKTA_SSO_URL=xxx
OKTA_ISSUER=xxx
FRONTEND_URL=http://localhost:3000
REACT_APP_API_URL=http://localhost:8000

perl
Copy code

### 2. Start
```bash
docker compose up --build
Frontend: http://localhost:3000
Backend: http://localhost:8000/docs

☁️ Deploy to EC2

git clone https://github.com/palakbansal8810/auth_platform.git
cd auth_platform
docker compose up -d --build


Nginx handles HTTPS and routing.

🔐 Security Notes

- Secrets are stored in .env (never committed)

- JWT is used for session authentication

- HTTPS enforced via Nginx

