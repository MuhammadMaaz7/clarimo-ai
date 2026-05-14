# Installation Guide

This guide will help you set up Clarimo AI on your local development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software
- **Node.js** (v18.0.0 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download](https://www.python.org/)
- **MongoDB** (v4.4 or higher) - [Download](https://www.mongodb.com/try/download/community)
- **Git** - [Download](https://git-scm.com/)

### Optional Software
- **MongoDB Compass** - GUI for MongoDB (recommended)
- **Postman** - API testing tool
- **VS Code** - Recommended IDE

## System Requirements

### Minimum Requirements
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Recommended Requirements
- **RAM**: 8 GB or more
- **Storage**: 5 GB free space
- **CPU**: Multi-core processor

## Installation Steps

### 1. Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd clarimo-ai

# Verify the structure
ls -la
```

You should see:
```
clarimo-ai/
├── Backend/
├── Frontend/
├── docs/
└── README.md
```

### 2. MongoDB Setup

#### Option A: Local MongoDB Installation

1. **Install MongoDB Community Edition**
   - Windows: Run the installer and follow the wizard
   - macOS: `brew install mongodb-community`
   - Linux: Follow [official guide](https://docs.mongodb.com/manual/administration/install-on-linux/)

2. **Start MongoDB Service**
   ```bash
   # Windows (as Administrator)
   net start MongoDB
   
   # macOS
   brew services start mongodb-community
   
   # Linux
   sudo systemctl start mongod
   ```

3. **Verify MongoDB is Running**
   ```bash
   mongosh
   # Should connect successfully
   ```

#### Option B: MongoDB Atlas (Cloud)

1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier available)
3. Get your connection string
4. Whitelist your IP address

### 3. Backend Setup

```bash
# Navigate to Backend directory
cd Backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### Install Additional Dependencies

```bash
# For GPU support (optional, for faster embeddings)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For development tools
pip install black flake8 pytest pytest-asyncio pytest-cov
```

#### Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Required Environment Variables:**

```env
# Database Configuration
MONGODB_URL=mongodb://localhost:27017/clarimo_ai

# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_V1_STR=/api
PROJECT_NAME=Clarimo AI
DEBUG=True

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Reddit API (for Problem Discovery)
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=Clarimo:v1.0.0 (by /u/yourusername)

# OpenAI API (for AI features)
OPENAI_API_KEY=your-openai-api-key

# Groq API (for fast inference)
GROQ_API_KEY=your-groq-api-key

# OpenRouter API (alternative LLM provider)
OPENROUTER_API_KEY=your-openrouter-api-key

# HuggingFace (for local models)
HF_MODEL=google/flan-t5-base
```

#### Verify Backend Installation

```bash
# Run the backend server
python run.py

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

Visit http://localhost:8000/docs to see the API documentation.

### 4. Frontend Setup

Open a new terminal window:

```bash
# Navigate to Frontend directory
cd Frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with your configuration
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Required Environment Variables:**

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# Application Configuration
VITE_APP_NAME=Clarimo AI
VITE_APP_VERSION=1.0.0
```

#### Verify Frontend Installation

```bash
# Start the development server
npm run dev

# You should see:
# VITE v7.x.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/
```

Visit http://localhost:5173 to see the application.

## Post-Installation Steps

### 1. Create Initial Database Collections

The application will automatically create collections on first use, but you can manually create them:

```bash
# Connect to MongoDB
mongosh

# Switch to database
use clarimo_ai

# Create collections
db.createCollection("users")
db.createCollection("problems")
db.createCollection("ideas")
db.createCollection("validations")
db.createCollection("products")
db.createCollection("analyses")
```

### 2. Create Test User (Optional)

```bash
# Use the API to create a test user
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

### 3. Verify All Services

1. **Backend API**: http://localhost:8000/docs ✅
2. **Frontend App**: http://localhost:5173 ✅
3. **MongoDB**: `mongosh` should connect ✅

## Troubleshooting

### MongoDB Connection Issues

**Error**: `MongoServerError: Authentication failed`

**Solution**:
```bash
# Check MongoDB is running
mongosh

# If using authentication, update connection string:
MONGODB_URL=mongodb://username:password@localhost:27017/clarimo_ai
```

### Python Virtual Environment Issues

**Error**: `venv\Scripts\activate : cannot be loaded because running scripts is disabled`

**Solution** (Windows PowerShell):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Find process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### npm Install Fails

**Error**: `EACCES: permission denied`

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
```

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'xxx'`

**Solution**:
```bash
# Ensure virtual environment is activated
# Then reinstall requirements
pip install -r requirements.txt
```

## Verification Checklist

- [ ] MongoDB is running and accessible
- [ ] Backend server starts without errors
- [ ] Backend API docs are accessible at http://localhost:8000/docs
- [ ] Frontend development server starts without errors
- [ ] Frontend app loads at http://localhost:5173
- [ ] Can create a new user account
- [ ] Can log in with created account
- [ ] Dashboard loads after login

## Next Steps

Once installation is complete:

1. Read the [Quick Start Guide](./QUICK_START.md)
2. Review the [Configuration Guide](./CONFIGURATION.md)
3. Explore the [API Documentation](./API_DOCUMENTATION.md)
4. Check out the [Development Guide](./BACKEND_DEVELOPMENT.md)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](./TROUBLESHOOTING.md)
2. Review the [FAQ](./FAQ.md)
3. Search existing GitHub issues
4. Create a new issue with:
   - Your OS and version
   - Python and Node.js versions
   - Error messages and logs
   - Steps to reproduce

---

**Installation Complete!** 🎉

You're now ready to start developing with Clarimo AI.
