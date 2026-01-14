## Authentication Flow

Users can authenticate using:
- Local email/password
- Google OAuth
- Okta SAML

All providers link to one user account using email.

## Database Schema

Users table:
- id
- email
- name

Auth Providers table:
- user_id
- provider
- provider_user_id
- password_hash

One user → multiple providers

## Security
- JWT-based sessions
- Passwords hashed using bcrypt
- OAuth handled by Authlib
- SAML handled via XML validation

## Architecture

Browser → Nginx → Frontend  
Browser → Nginx → Backend → PostgreSQL
