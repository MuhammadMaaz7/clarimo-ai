# 🚀 Clarimo AI

**AI-Powered Startup Accelerator Platform**

Transform your startup ideas into successful ventures with AI-powered insights, problem discovery, and validation tools designed for entrepreneurs.

![Clarimo AI](https://img.shields.io/badge/Status-Active%20Development-brightgreen)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-green)

## ✨ Features

- **🔍 Problem Discovery**: Uncover real problems from online communities
- **🤖 AI-Powered Analysis**: Validate ideas with intelligent market research  
- **📈 Growth Strategies**: Get personalized roadmaps to success
- **👥 Community Support**: Connect with fellow entrepreneurs
- **🎯 Idea Validation**: Get instant feedback on your startup concepts
- **📊 Competitor Analysis**: Understand your competitive landscape
- **🎯 Customer Finding**: Identify and reach your target audience
- **📋 Launch Planning**: Create comprehensive go-to-market strategies

## 🏗️ Architecture

```
Clarimo AI/
├── Frontend/                 # React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── contexts/       # React contexts (Auth, etc.)
│   │   ├── hooks/          # Custom React hooks
│   │   └── lib/            # Utility functions
│   ├── public/             # Static assets
│   └── package.json
│
├── Backend/                 # FastAPI + Python
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality (auth, config)
│   │   ├── db/             # Database models and connection
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt
│   └── run.py
│
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **MongoDB** (local or cloud instance)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd clarimo-ai
```

### 2. Backend Setup

```bash
cd Backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Start the backend server
python run.py
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd Frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local with your configuration

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the `Backend/` directory:

```env
# Database
MONGODB_URL=mongodb://localhost:27017/clarimo_ai

# JWT Configuration
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=Clarimo AI

# External APIs (optional)
OPENAI_API_KEY=your-openai-key
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
```

### Frontend Environment Variables

Create a `.env.local` file in the `Frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Clarimo AI
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

- `POST /auth/signup` - User registration
- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user
- `POST /problems/discover` - Discover problems from communities
- `GET /problems` - List discovered problems

## 🛠️ Development

### Frontend Commands

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

### Backend Commands

```bash
python run.py                    # Start development server
uvicorn app.main:app --reload   # Alternative start command
pytest                          # Run tests
black .                         # Format code
flake8                          # Lint code
```

## 🎨 Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Vite** - Build tool
- **React Router** - Navigation
- **React Query** - Data fetching
- **Zustand** - State management

### Backend
- **FastAPI** - Web framework
- **Python 3.8+** - Programming language
- **MongoDB** - Database
- **JWT** - Authentication
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

## 🚀 Deployment

### Frontend (Vercel/Netlify)

```bash
npm run build
# Deploy the dist/ folder
```

### Backend (Railway/Heroku)

```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Deploy using your preferred platform
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern web technologies
- Inspired by the startup ecosystem
- Powered by AI and community insights

---

**Made with for entrepreneurs worldwide**