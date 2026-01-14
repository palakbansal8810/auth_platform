# Authentication Platform

A secure multi-provider authentication system supporting Google OAuth 2.0, Okta SAML 2.0, and local email/password authentication.

## Architecture

- **Backend**: FastAPI (Python) with PostgreSQL
- **Frontend**: React with React Router
- **Database**: PostgreSQL 15
- **Reverse Proxy**: Nginx
- **Deployment**: Docker + Docker Compose

## Features

- ✅ Google OAuth 2.0 Authentication
- ✅ Okta SAML 2.0 Authentication
- ✅ Email/Password Authentication
- ✅ JWT-based session management
- ✅ Unified user database with duplicate handling
- ✅ Dockerized deployment
- ✅ Nginx reverse proxy
- ✅ SSL/HTTPS ready

## Project Structure

```
auth-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── users.py             # User endpoints
│   │   └── auth/
│   │       ├── google.py        # Google OAuth handler
│   │       ├── okta.py          # Okta SAML handler
│   │       └── local.py         # Local auth handler
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── pages/
│   │       ├── Login.js         # Login page
│   │       ├── Dashboard.js     # User dashboard
│   │       └── AuthCallback.js  # OAuth callback
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── nginx/
│   └── default.conf             # Nginx configuration
├── docker-compose.yml
├── .env.example
└── README.md
```

## Local Development Setup

### Prerequisites

- Docker & Docker Compose
- Google Cloud Console project (for OAuth)
- Okta account (for SAML)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd auth-platform
```

### Step 2: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/authdb

# Security
SECRET_KEY=your-random-secret-key-minimum-32-characters

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Okta SAML
OKTA_SSO_URL=https://your-domain.okta.com/app/your-app-id/sso/saml
OKTA_ISSUER=http://localhost/auth/okta/callback

# Frontend
FRONTEND_URL=http://localhost
```

### Step 3: Setup Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create OAuth 2.0 Client ID
5. Application type: Web application
6. Authorized redirect URIs:
   - `http://localhost/auth/google/callback` (local)
   - `https://yourdomain.com/auth/google/callback` (production)
7. Copy Client ID and Client Secret to `.env`

### Step 4: Setup Okta SAML

1. Log into [Okta Admin Console](https://admin.okta.com)
2. Applications → Create App Integration
3. Select SAML 2.0
4. Configure:
   - Single sign on URL: `http://localhost/auth/okta/callback`
   - Audience URI: `http://localhost/auth/okta/callback`
   - Attribute Statements:
     - email: user.email
     - name: user.firstName + user.lastName
5. Copy SSO URL to `.env` as `OKTA_SSO_URL`

### Step 5: Run Application

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost/api
- Database: localhost:5432

### Step 6: Test Authentication

1. Register with email/password
2. Login with Google
3. Login with Okta
4. Verify user profile displays correctly

## Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    provider VARCHAR NOT NULL,  -- 'local', 'google', 'okta'
    provider_id VARCHAR,
    hashed_password VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Duplicate Account Handling

- Users are identified by email (unique constraint)
- If same email signs in via different providers:
  - First login creates the account with that provider
  - Subsequent logins update provider info but keep same user record
- This allows seamless switching between auth methods

## API Endpoints

### Authentication

```
POST   /auth/local/register     - Register new user
POST   /auth/local/login        - Login with email/password
GET    /auth/google/login       - Initiate Google OAuth
GET    /auth/google/callback    - Google OAuth callback
GET    /auth/okta/login         - Initiate Okta SAML
POST   /auth/okta/callback      - Okta SAML callback
```

### User Management

```
GET    /api/user/profile        - Get current user profile (requires auth)
```

## AWS EC2 Deployment

### Step 1: Launch EC2 Instance

```bash
# Instance type: t2.medium or larger
# AMI: Ubuntu 22.04 LTS
# Security group: Allow ports 22, 80, 443
```

### Step 2: Connect and Install Dependencies

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
```

### Step 3: Setup Application

```bash
# Clone repository
git clone <your-repo-url>
cd auth-platform

# Configure environment
nano .env
# Update all values for production:
# - Use strong SECRET_KEY
# - Update FRONTEND_URL to your domain
# - Update OAuth redirect URIs in Google/Okta
```

### Step 4: Configure Domain and SSL

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Update nginx config for your domain
sudo nano nginx/default.conf
```

Update nginx config:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Backend proxy
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
    
    location /auth/ {
        proxy_pass http://backend:8000/auth/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
    }
}
```

### Step 5: Obtain SSL Certificate

```bash
# Get certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Update docker-compose to mount certificates
```

Update `docker-compose.yml` nginx service:

```yaml
nginx:
  image: nginx:alpine
  volumes:
    - ./nginx/default.conf:/etc/nginx/conf.d/default.conf
    - /etc/letsencrypt:/etc/letsencrypt:ro
  ports:
    - "80:80"
    - "443:443"
```

### Step 6: Deploy Application

```bash
# Start application
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Setup auto-renewal for SSL
sudo crontab -e
# Add: 0 0 * * 0 certbot renew --quiet && docker-compose restart nginx
```

### Step 7: Update OAuth Redirect URIs

Update in Google Cloud Console and Okta:
- `https://yourdomain.com/auth/google/callback`
- `https://yourdomain.com/auth/okta/callback`

## Authentication Flow Diagrams

### Google OAuth Flow
```
User → Frontend → /auth/google/login
  → Google OAuth Consent
  → Google Callback → /auth/google/callback
  → Backend creates/updates user
  → Returns JWT token
  → Frontend stores token
  → Redirect to Dashboard
```

### Okta SAML Flow
```
User → Frontend → /auth/okta/login
  → Backend generates SAML Request
  → Okta Authentication
  → SAML Response → /auth/okta/callback
  → Backend parses SAML, creates/updates user
  → Returns JWT token
  → Frontend stores token
  → Redirect to Dashboard
```

### Local Auth Flow
```
User → Frontend → /auth/local/register or /login
  → Backend validates credentials
  → Creates user (register) or verifies password (login)
  → Returns JWT token
  → Frontend stores token
  → Redirect to Dashboard
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` file
2. **Secret Key**: Use strong random key (32+ characters)
3. **HTTPS Only**: Always use SSL in production
4. **Password Hashing**: Using bcrypt for local passwords
5. **JWT Expiration**: Tokens expire after 7 days
6. **CORS**: Configure appropriately for production
7. **Database**: Use strong passwords, restrict network access

## Troubleshooting

### Database Connection Issues
```bash
# Check database is running
docker-compose ps db

# Check connection
docker-compose exec db psql -U postgres -d authdb -c "\dt"
```

### OAuth Redirect Issues
- Verify redirect URIs match exactly in provider console
- Check FRONTEND_URL in environment variables
- Ensure HTTPS in production

### SSL Certificate Issues
```bash
# Test certificate
sudo certbot certificates

# Renew manually
sudo certbot renew
```

## Monitoring

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Check resource usage
docker stats
```

## Backup

```bash
# Backup database
docker-compose exec db pg_dump -U postgres authdb > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U postgres authdb
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify environment variables
3. Test OAuth credentials
4. Check network connectivity

## License

MIT License