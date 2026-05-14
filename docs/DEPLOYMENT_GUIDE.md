# Deployment Guide

This guide covers deploying Clarimo AI to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
3. [Backend Deployment (Railway)](#backend-deployment-railway)
4. [Database Setup (MongoDB Atlas)](#database-setup-mongodb-atlas)
5. [Environment Configuration](#environment-configuration)
6. [Post-Deployment Steps](#post-deployment-steps)
7. [Monitoring & Maintenance](#monitoring--maintenance)

## Pre-Deployment Checklist

Before deploying to production:

- [ ] All tests passing (`pytest` and `npm test`)
- [ ] Code reviewed and approved
- [ ] Environment variables documented
- [ ] Database backup strategy in place
- [ ] SSL certificates ready
- [ ] Domain names configured
- [ ] Error monitoring setup (Sentry recommended)
- [ ] Performance monitoring configured
- [ ] Security audit completed
- [ ] Documentation updated

## Frontend Deployment (Vercel)

### Step 1: Prepare Frontend

```bash
cd Frontend

# Test production build locally
npm run build
npm run preview

# Verify build output
ls -la dist/
```

### Step 2: Deploy to Vercel

#### Option A: Vercel Dashboard (Recommended)

1. Visit [vercel.com/new](https://vercel.com/new)
2. Click "Import Project"
3. Select your Git repository
4. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `Frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Click "Deploy"

#### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
cd Frontend
vercel

# Deploy to production
vercel --prod
```

### Step 3: Configure Environment Variables

In Vercel Dashboard → Settings → Environment Variables:

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_BASE_URL` | `https://your-backend.railway.app/api` | Production |
| `VITE_APP_NAME` | `Clarimo AI` | All |
| `VITE_APP_VERSION` | `1.0.0` | All |

### Step 4: Configure Custom Domain

1. Go to Settings → Domains
2. Add your domain (e.g., `app.clarimo.ai`)
3. Update DNS records as instructed
4. Wait for SSL certificate provisioning (automatic)

### Step 5: Verify Deployment

- [ ] Site loads at production URL
- [ ] All pages accessible
- [ ] API calls work correctly
- [ ] Authentication works
- [ ] No console errors
- [ ] Performance is acceptable

---

## Backend Deployment (Railway)

### Step 1: Prepare Backend

```bash
cd Backend

# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Test locally
python run.py
```

### Step 2: Create Railway Project

1. Visit [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Select `Backend` as root directory

### Step 3: Configure Build Settings

Railway should auto-detect Python. Verify:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 4: Configure Environment Variables

In Railway Dashboard → Variables:

```env
# Database
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/clarimo_ai

# JWT
SECRET_KEY=your-super-secret-production-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_STR=/api
PROJECT_NAME=Clarimo AI
DEBUG=False

# CORS
CORS_ORIGINS=https://app.clarimo.ai,https://clarimo.ai

# External APIs
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...

# Reddit API
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=Clarimo:v1.0.0

# HuggingFace
HF_MODEL=google/flan-t5-base
```

### Step 5: Deploy

1. Click "Deploy"
2. Wait for build to complete
3. Railway will provide a URL: `https://your-app.railway.app`

### Step 6: Configure Custom Domain

1. Go to Settings → Domains
2. Add custom domain (e.g., `api.clarimo.ai`)
3. Update DNS records:
   ```
   Type: CNAME
   Name: api
   Value: your-app.railway.app
   ```

---

## Database Setup (MongoDB Atlas)

### Step 1: Create Cluster

1. Visit [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up/Login
3. Create a new cluster (Free tier available)
4. Choose cloud provider and region
5. Wait for cluster creation (~5 minutes)

### Step 2: Configure Security

1. **Database Access**:
   - Create database user
   - Set username and password
   - Grant read/write permissions

2. **Network Access**:
   - Add IP addresses
   - For Railway: Add `0.0.0.0/0` (allow from anywhere)
   - For production: Restrict to specific IPs

### Step 3: Get Connection String

1. Click "Connect"
2. Choose "Connect your application"
3. Copy connection string:
   ```
   mongodb+srv://username:<password>@cluster.mongodb.net/clarimo_ai
   ```
4. Replace `<password>` with your actual password

### Step 4: Create Database and Collections

```javascript
// Connect using MongoDB Compass or mongosh
use clarimo_ai

// Create collections
db.createCollection("users")
db.createCollection("problems")
db.createCollection("ideas")
db.createCollection("validations")
db.createCollection("products")
db.createCollection("analyses")
db.createCollection("customer_insights")
db.createCollection("launch_plans")
db.createCollection("gtm_strategies")

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true })
db.problems.createIndex({ "user_id": 1, "created_at": -1 })
db.ideas.createIndex({ "user_id": 1, "created_at": -1 })
db.validations.createIndex({ "idea_id": 1, "created_at": -1 })
```

### Step 5: Configure Backups

1. Go to Cluster → Backup
2. Enable continuous backups
3. Configure backup schedule
4. Set retention policy

---

## Environment Configuration

### Production Environment Variables

#### Frontend (.env.production)

```env
VITE_API_BASE_URL=https://api.clarimo.ai/api
VITE_APP_NAME=Clarimo AI
VITE_APP_VERSION=1.0.0
```

#### Backend (.env)

```env
# Database
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/clarimo_ai

# JWT
SECRET_KEY=your-super-secret-production-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_STR=/api
PROJECT_NAME=Clarimo AI
DEBUG=False

# CORS (comma-separated)
CORS_ORIGINS=https://app.clarimo.ai,https://clarimo.ai

# External APIs
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=Clarimo:v1.0.0

# HuggingFace
HF_MODEL=google/flan-t5-base

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/clarimo/app.log

# Performance
WORKERS=4
MAX_CONNECTIONS=100
```

---

## Post-Deployment Steps

### 1. Update CORS Settings

Ensure backend CORS includes production domains:

```python
# Backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.clarimo.ai",
        "https://clarimo.ai",
        "https://www.clarimo.ai"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Test Production Deployment

```bash
# Test API health
curl https://api.clarimo.ai/health

# Test authentication
curl -X POST https://api.clarimo.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test frontend
open https://app.clarimo.ai
```

### 3. Setup Error Monitoring

#### Sentry Integration

```bash
# Install Sentry
pip install sentry-sdk[fastapi]
npm install @sentry/react
```

```python
# Backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

```typescript
// Frontend/src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 1.0,
});
```

### 4. Setup Performance Monitoring

- Enable Vercel Analytics
- Enable Railway Metrics
- Configure MongoDB Atlas monitoring
- Setup uptime monitoring (UptimeRobot, Pingdom)

### 5. Configure CDN

For static assets:
- Use Cloudflare CDN
- Configure caching rules
- Enable compression

### 6. Setup SSL/TLS

- Vercel: Automatic SSL
- Railway: Automatic SSL
- Custom domains: Let's Encrypt

---

## Monitoring & Maintenance

### Health Checks

Create health check endpoints:

```python
# Backend/app/api/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }
```

### Logging

Configure structured logging:

```python
# Backend/app/core/logging_config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/clarimo/app.log'),
        logging.StreamHandler()
    ]
)
```

### Backup Strategy

1. **Database Backups**:
   - Automated daily backups (MongoDB Atlas)
   - Weekly full backups
   - 30-day retention

2. **Code Backups**:
   - Git repository (GitHub)
   - Tagged releases

3. **Environment Backups**:
   - Document all environment variables
   - Store securely (1Password, AWS Secrets Manager)

### Monitoring Checklist

- [ ] Uptime monitoring configured
- [ ] Error tracking active (Sentry)
- [ ] Performance monitoring enabled
- [ ] Database monitoring active
- [ ] Log aggregation setup
- [ ] Alert notifications configured
- [ ] Backup verification scheduled

### Scaling Considerations

#### Horizontal Scaling

```yaml
# Railway: Increase replicas
replicas: 3

# Vercel: Automatic scaling
```

#### Database Scaling

- Enable MongoDB Atlas auto-scaling
- Configure read replicas
- Implement caching (Redis)

#### Performance Optimization

- Enable CDN for static assets
- Implement API response caching
- Optimize database queries
- Use connection pooling

---

## Rollback Procedure

If deployment fails:

### Frontend Rollback

1. Go to Vercel Dashboard → Deployments
2. Find previous working deployment
3. Click "..." → "Promote to Production"

### Backend Rollback

1. Go to Railway Dashboard → Deployments
2. Select previous deployment
3. Click "Redeploy"

### Database Rollback

1. Go to MongoDB Atlas → Backup
2. Select backup point
3. Restore to cluster

---

## Security Checklist

- [ ] HTTPS enforced
- [ ] Environment variables secured
- [ ] API keys rotated regularly
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] SQL injection prevention
- [ ] XSS protection enabled
- [ ] CSRF protection configured
- [ ] Security headers set

---

## Troubleshooting

### Common Issues

**Issue**: API calls fail with CORS error

**Solution**:
```python
# Update CORS origins in backend
CORS_ORIGINS=https://app.clarimo.ai
```

**Issue**: Environment variables not loading

**Solution**:
- Verify variables are set in platform dashboard
- Redeploy after adding variables
- Check variable names (case-sensitive)

**Issue**: Database connection fails

**Solution**:
- Verify MongoDB connection string
- Check IP whitelist in MongoDB Atlas
- Verify database user permissions

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Environment variables documented
- [ ] Backup strategy in place

### Deployment
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Railway
- [ ] Database configured on MongoDB Atlas
- [ ] Environment variables set
- [ ] Custom domains configured
- [ ] SSL certificates active

### Post-Deployment
- [ ] Health checks passing
- [ ] Error monitoring active
- [ ] Performance monitoring enabled
- [ ] Backups configured
- [ ] Team notified
- [ ] Documentation updated

---

**Last Updated**: May 13, 2026
