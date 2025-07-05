# Keycloak Setup Guide

This guide explains how to set up Keycloak for the ITDO ERP system.

## Prerequisites

- Docker or Podman installed
- Access to Keycloak admin console
- ITDO ERP backend running

## Quick Start with Docker

### 1. Start Keycloak

```bash
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak:23.0 \
  start-dev
```

### 2. Access Admin Console

Open http://localhost:8080 and login with:
- Username: `admin`
- Password: `admin`

## Realm Configuration

### 1. Create Realm

1. Click on the realm dropdown (top-left)
2. Click "Create Realm"
3. Enter:
   - Realm name: `itdo-erp`
   - Enabled: ON
4. Click "Create"

### 2. Configure Realm Settings

Navigate to Realm Settings:

#### General Tab
- Display name: `ITDO ERP`
- HTML Display name: `<b>ITDO ERP</b>`

#### Login Tab
- User registration: OFF (managed by admin)
- Forgot password: ON
- Remember me: ON
- Login with email: ON

#### Tokens Tab
- Access Token Lifespan: 24 hours
- Refresh Token Lifespan: 7 days

## Client Configuration

### 1. Create Client

1. Navigate to Clients → Create client
2. General Settings:
   - Client type: `OpenID Connect`
   - Client ID: `itdo-erp-backend`
3. Click "Next"
4. Capability config:
   - Client authentication: ON
   - Authorization: OFF
   - Standard flow: ON
   - Direct access grants: ON
5. Click "Next"
6. Login settings:
   - Valid redirect URIs: 
     ```
     http://localhost:8000/*
     http://localhost:3000/*
     ```
   - Valid post logout redirect URIs: `+`
   - Web origins: `+`
7. Click "Save"

### 2. Get Client Secret

1. Navigate to Clients → `itdo-erp-backend`
2. Go to "Credentials" tab
3. Copy the "Client secret"
4. Update your `.env` file:
   ```env
   KEYCLOAK_CLIENT_SECRET=<copied-secret>
   ```

## User and Role Setup

### 1. Create Roles

Navigate to Realm roles → Create role:

1. **Admin Role**
   - Role name: `admin`
   - Description: `System administrator with full access`

2. **Manager Role**
   - Role name: `manager`
   - Description: `Manager with approval and reporting access`

3. **User Role**
   - Role name: `user`
   - Description: `Regular user with basic access`

### 2. Create Users

Navigate to Users → Add user:

#### Admin User
1. Username: `admin@itdo.jp`
2. Email: `admin@itdo.jp`
3. Email verified: ON
4. First name: `Admin`
5. Last name: `User`
6. Click "Create"
7. Go to "Credentials" tab:
   - Set password: `admin123`
   - Temporary: OFF
8. Go to "Role mapping" tab:
   - Assign roles: `admin`, `user`

#### Manager User
1. Username: `manager@itdo.jp`
2. Email: `manager@itdo.jp`
3. Follow similar steps
4. Assign roles: `manager`, `user`

#### Regular User
1. Username: `user@itdo.jp`
2. Email: `user@itdo.jp`
3. Follow similar steps
4. Assign role: `user`

## Frontend Client (Optional)

If your frontend needs direct Keycloak access:

### Create Public Client

1. Navigate to Clients → Create client
2. General Settings:
   - Client type: `OpenID Connect`
   - Client ID: `itdo-erp-frontend`
3. Capability config:
   - Client authentication: OFF (public client)
   - Standard flow: ON
   - Direct access grants: OFF
4. Login settings:
   - Valid redirect URIs: `http://localhost:3000/*`
   - Valid post logout redirect URIs: `+`
   - Web origins: `+`

## Testing the Integration

### 1. Test OAuth2 Flow

```bash
# Get the authorization URL
curl -i http://localhost:8000/api/v1/auth/keycloak/login
```

This should redirect to Keycloak login page.

### 2. Test with Postman

1. Create new OAuth2 request
2. Configuration:
   - Grant Type: `Authorization Code`
   - Auth URL: `http://localhost:8080/auth/realms/itdo-erp/protocol/openid-connect/auth`
   - Token URL: `http://localhost:8080/auth/realms/itdo-erp/protocol/openid-connect/token`
   - Client ID: `itdo-erp-backend`
   - Client Secret: `<your-secret>`
   - Scope: `openid email profile`

### 3. Test Direct Grant (Development Only)

```bash
# Get token directly
curl -X POST http://localhost:8080/auth/realms/itdo-erp/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=itdo-erp-backend" \
  -d "client_secret=<your-secret>" \
  -d "username=admin@itdo.jp" \
  -d "password=admin123"
```

## Production Deployment

### 1. Use Production Database

Replace the development database with PostgreSQL:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak
    volumes:
      - postgres_data:/var/lib/postgresql/data

  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak
      KC_HOSTNAME: auth.itdo-erp.jp
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: changeme
    command: start
    depends_on:
      - postgres
    ports:
      - "8443:8443"

volumes:
  postgres_data:
```

### 2. Enable HTTPS

1. Generate or obtain SSL certificates
2. Mount certificates in Keycloak container
3. Update KC_HTTPS_* environment variables

### 3. Configure Reverse Proxy

Example Nginx configuration:

```nginx
server {
    listen 443 ssl;
    server_name auth.itdo-erp.jp;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass https://keycloak:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Maintenance

### Health Check

```bash
curl http://localhost:8080/auth/realms/itdo-erp/.well-known/openid-configuration
```

### Backup

1. Export realm configuration:
   ```bash
   docker exec keycloak /opt/keycloak/bin/kc.sh export \
     --file /tmp/realm-export.json \
     --realm itdo-erp
   ```

2. Backup database regularly

### Updates

1. Check release notes: https://www.keycloak.org/docs/latest/release_notes/
2. Test updates in staging environment
3. Backup before updating
4. Update using new Docker image version

## Troubleshooting

### Common Issues

1. **CORS errors**
   - Check Web Origins in client settings
   - Ensure backend CORS includes Keycloak URL

2. **Invalid redirect URI**
   - Verify Valid Redirect URIs in client settings
   - Check for exact match including protocol

3. **Token validation fails**
   - Verify client secret is correct
   - Check token expiration settings
   - Ensure time sync between servers

4. **SSL/HTTPS issues**
   - In development, Keycloak uses self-signed certificates
   - For production, use proper certificates
   - Update KEYCLOAK_CALLBACK_URL to use HTTPS

### Debug Mode

Enable detailed logging:

```bash
docker run -d \
  --name keycloak \
  -p 8080:8080 \
  -e KEYCLOAK_ADMIN=admin \
  -e KEYCLOAK_ADMIN_PASSWORD=admin \
  -e KC_LOG_LEVEL=DEBUG \
  quay.io/keycloak/keycloak:23.0 \
  start-dev
```