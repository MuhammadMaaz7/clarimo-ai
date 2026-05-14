# System Architecture

## Overview

Clarimo AI is a full-stack web application built with a modern microservices-inspired architecture, featuring a React frontend and FastAPI backend with MongoDB database.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         React Frontend (TypeScript + Vite)            │  │
│  │  - Landing Page  - Dashboard  - Module Interfaces    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS/REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           FastAPI Backend (Python 3.8+)              │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │  │
│  │  │ Auth API   │  │ Module APIs│  │ Shared APIs│    │  │
│  │  └────────────┘  └────────────┘  └────────────┘    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ MongoDB Driver
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MongoDB Database                         │  │
│  │  - Users  - Problems  - Ideas  - Validations         │  │
│  │  - Products  - Analyses  - Insights  - Plans         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ External APIs
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ OpenAI   │  │  Groq    │  │ Reddit   │  │ OpenRouter│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Frontend Architecture

```
Frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Base UI components (buttons, cards, etc.)
│   │   ├── landing/        # Landing page specific components
│   │   ├── shared/         # Shared components across modules
│   │   └── [module]/       # Module-specific components
│   │
│   ├── pages/              # Page components (routes)
│   │   ├── Landing.tsx     # Landing page
│   │   ├── Dashboard.tsx   # Main dashboard
│   │   ├── Login.tsx       # Authentication pages
│   │   └── [Module].tsx    # Module pages
│   │
│   ├── contexts/           # React Context providers
│   │   ├── AuthContext.tsx         # Authentication state
│   │   ├── ValidationContext.tsx   # Validation state
│   │   └── CompetitorContext.tsx   # Competitor analysis state
│   │
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts              # Authentication hook
│   │   ├── useIdeaValidation.ts    # Validation hook
│   │   └── useDashboardStats.ts    # Dashboard data hook
│   │
│   ├── lib/                # Utility libraries
│   │   ├── api.ts          # API client
│   │   └── utils.ts        # Helper functions
│   │
│   ├── services/           # Business logic services
│   │   ├── TokenManager.ts         # JWT token management
│   │   ├── ActivityDetector.ts     # User activity tracking
│   │   └── chatService.ts          # Chat functionality
│   │
│   └── types/              # TypeScript type definitions
│       └── global.d.ts     # Global type declarations
│
├── public/                 # Static assets
│   ├── logo.png           # Application logo
│   └── favicon.ico        # Browser favicon
│
└── Configuration files
    ├── vite.config.js     # Vite bundler configuration
    ├── tailwind.config.js # Tailwind CSS configuration
    └── tsconfig.json      # TypeScript configuration
```

### Backend Architecture

```
Backend/
├── app/
│   ├── api/                        # API route handlers
│   │   ├── routes_auth.py         # Authentication endpoints
│   │   ├── problem_discovery/     # Module 1: Problem Discovery
│   │   ├── idea_validation/       # Module 2: Idea Validation
│   │   ├── competitor_intelligence/ # Module 3: Competitor Analysis
│   │   ├── customer_insights/     # Module 4: Customer Insights
│   │   ├── launch_planning/       # Module 5: Launch Planning
│   │   ├── gtm/                   # Module 6: GTM Strategy
│   │   └── chat/                  # Chat functionality
│   │
│   ├── core/                      # Core functionality
│   │   ├── config.py             # Application configuration
│   │   ├── security.py           # Security utilities (JWT, hashing)
│   │   ├── dependencies.py       # FastAPI dependencies
│   │   ├── llm_config.py         # LLM provider configuration
│   │   └── logging_config.py     # Logging configuration
│   │
│   ├── db/                        # Database layer
│   │   ├── database.py           # MongoDB connection
│   │   ├── models/               # Database models
│   │   │   ├── user_model.py
│   │   │   ├── problem_model.py
│   │   │   ├── idea_model.py
│   │   │   └── [other models]
│   │   └── schemas/              # Pydantic schemas
│   │       └── user_schema.py
│   │
│   ├── services/                  # Business logic
│   │   ├── shared/               # Shared services
│   │   │   ├── llm_service.py   # Unified LLM service
│   │   │   └── embedding_service.py
│   │   ├── problem_discovery/    # Module 1 services
│   │   ├── idea_validation/      # Module 2 services
│   │   ├── competitor_intelligence/ # Module 3 services
│   │   ├── customer_insights/    # Module 4 services
│   │   ├── launch_planning/      # Module 5 services
│   │   └── gtm/                  # Module 6 services
│   │
│   ├── middleware/               # Custom middleware
│   │   └── error_handler.py     # Global error handling
│   │
│   ├── utils/                    # Utility functions
│   │   ├── error_handling.py    # Error utilities
│   │   └── response_builder.py  # Response formatting
│   │
│   └── main.py                   # FastAPI application entry point
│
├── data/                         # Data storage
│   ├── embeddings/              # Vector embeddings
│   ├── reddit_posts/            # Scraped Reddit data
│   └── outputs/                 # Generated outputs
│
├── logs/                        # Application logs
│
└── Configuration files
    ├── requirements.txt         # Python dependencies
    ├── .env                    # Environment variables
    └── run.py                  # Application runner
```

## Data Flow

### 1. Authentication Flow

```
User → Frontend → POST /api/auth/login → Backend
                                          ↓
                                    Verify credentials
                                          ↓
                                    Generate JWT token
                                          ↓
Frontend ← JWT token + user data ← Backend
    ↓
Store token in localStorage
    ↓
Include token in subsequent requests
```

### 2. Problem Discovery Flow

```
User Input → Frontend → POST /api/user-input/
                              ↓
                        Backend validates input
                              ↓
                        Generate keywords
                              ↓
                        Fetch Reddit posts
                              ↓
                        Generate embeddings
                              ↓
                        Semantic filtering
                              ↓
                        Clustering
                              ↓
                        Extract pain points
                              ↓
                        Rank pain points
                              ↓
Frontend ← Results ← Store in MongoDB
```

### 3. Idea Validation Flow

```
Idea Submission → Frontend → POST /api/ideas/
                                   ↓
                             Store idea in DB
                                   ↓
                             POST /api/validations/validate
                                   ↓
                             LLM Service (with fallback)
                                   ↓
                             ┌─────┴─────┐
                             ↓           ↓
                        OpenRouter    Groq
                             ↓           ↓
                        HuggingFace (fallback)
                             ↓
                        Generate validation report
                             ↓
                        Store results
                             ↓
Frontend ← Validation results ← Backend
```

## Technology Stack

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.1 | UI framework |
| TypeScript | 5.9.3 | Type safety |
| Vite | 7.1.7 | Build tool |
| Tailwind CSS | 3.4.18 | Styling |
| React Router | 7.9.4 | Routing |
| Axios | 1.12.2 | HTTP client |
| Framer Motion | 12.38.0 | Animations |
| Lucide React | 0.545.0 | Icons |
| Recharts | 3.5.0 | Charts |

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | Latest | Web framework |
| Python | 3.8+ | Programming language |
| MongoDB | 4.4+ | Database |
| PyMongo | Latest | MongoDB driver |
| Pydantic | Latest | Data validation |
| JWT | Latest | Authentication |
| Sentence Transformers | Latest | Embeddings |
| FAISS | Latest | Vector search |
| Scikit-learn | Latest | ML algorithms |

### External Services

| Service | Purpose |
|---------|---------|
| OpenAI API | GPT models for text generation |
| Groq API | Fast LLM inference |
| OpenRouter API | Alternative LLM provider |
| Reddit API | Social media data scraping |
| HuggingFace | Local model fallback |

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────┐
│                   Security Layers                        │
├─────────────────────────────────────────────────────────┤
│  1. JWT Token Authentication                            │
│     - Access tokens (30 min expiry)                     │
│     - Secure token storage (localStorage)               │
│     - Token refresh mechanism                           │
├─────────────────────────────────────────────────────────┤
│  2. Password Security                                    │
│     - Bcrypt hashing (12 rounds)                        │
│     - No plain text storage                             │
│     - Password strength validation                      │
├─────────────────────────────────────────────────────────┤
│  3. API Security                                         │
│     - CORS configuration                                │
│     - Rate limiting (planned)                           │
│     - Input validation (Pydantic)                       │
├─────────────────────────────────────────────────────────┤
│  4. Data Security                                        │
│     - User data isolation                               │
│     - Secure environment variables                      │
│     - HTTPS in production                               │
└─────────────────────────────────────────────────────────┘
```

### Security Best Practices Implemented

1. **Password Hashing**: Bcrypt with salt rounds
2. **JWT Tokens**: Short-lived access tokens
3. **Input Validation**: Pydantic models for all inputs
4. **CORS**: Configured allowed origins
5. **Environment Variables**: Sensitive data in .env files
6. **Error Handling**: No sensitive data in error messages

## Scalability Considerations

### Current Architecture
- **Monolithic backend**: Single FastAPI application
- **Single database**: MongoDB instance
- **Synchronous processing**: Sequential task execution

### Future Scalability Options

1. **Horizontal Scaling**
   - Load balancer (Nginx/AWS ALB)
   - Multiple backend instances
   - Session management (Redis)

2. **Database Scaling**
   - MongoDB replica sets
   - Sharding for large datasets
   - Read replicas

3. **Async Processing**
   - Celery for background tasks
   - Redis/RabbitMQ message queue
   - Separate worker processes

4. **Caching Layer**
   - Redis for API responses
   - CDN for static assets
   - Database query caching

5. **Microservices Migration**
   - Separate services per module
   - API Gateway
   - Service mesh

## Performance Optimization

### Frontend Optimizations
- Code splitting (Vite)
- Lazy loading of routes
- Image optimization
- Bundle size optimization
- Tree shaking

### Backend Optimizations
- Database indexing
- Query optimization
- Connection pooling
- Response caching
- Async/await patterns

### Database Optimizations
- Compound indexes
- Projection queries
- Aggregation pipelines
- Connection pooling

## Monitoring & Logging

### Logging Strategy

```python
# Structured logging with levels
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical issues
```

### Log Storage
- **Development**: Console output
- **Production**: File-based logging in `logs/` directory

### Monitoring Points
1. API response times
2. Database query performance
3. External API call success rates
4. Error rates and types
5. User activity metrics

## Deployment Architecture

### Development Environment
```
Local Machine
├── Frontend (localhost:5173)
├── Backend (localhost:8000)
└── MongoDB (localhost:27017)
```

### Production Environment (Recommended)
```
Cloud Infrastructure
├── Frontend (Vercel/Netlify)
├── Backend (Railway/Heroku/AWS)
├── Database (MongoDB Atlas)
└── CDN (Cloudflare/AWS CloudFront)
```

## API Design Principles

### RESTful API Design
- Resource-based URLs
- HTTP methods (GET, POST, PUT, DELETE)
- Status codes (200, 201, 400, 401, 404, 500)
- JSON request/response format

### API Versioning
- URL-based versioning: `/api/v1/`
- Backward compatibility maintained

### Error Handling
- Consistent error response format
- Meaningful error messages
- Appropriate HTTP status codes

## Database Design Principles

### Document Structure
- Embedded documents for related data
- References for large or frequently updated data
- Denormalization for read performance

### Indexing Strategy
- Primary key (_id) automatic indexing
- Compound indexes for common queries
- Text indexes for search functionality

### Data Validation
- Schema validation at application level (Pydantic)
- MongoDB schema validation (optional)

## Conclusion

This architecture provides:
- ✅ **Scalability**: Can grow with user base
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Security**: Multiple security layers
- ✅ **Performance**: Optimized for speed
- ✅ **Reliability**: Error handling and logging
- ✅ **Flexibility**: Easy to add new features

---

**Last Updated**: May 13, 2026
