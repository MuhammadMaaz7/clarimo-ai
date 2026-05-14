# API Documentation

## Base URL

- **Development**: `http://localhost:8000/api`
- **Production**: `https://your-domain.com/api`

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

---

## Authentication Endpoints

### POST /auth/signup

Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response** (201):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2026-05-13T10:00:00Z"
  }
}
```

---

### POST /auth/login

Authenticate user and receive JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

---

### GET /auth/me

Get current authenticated user information.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2026-05-13T10:00:00Z"
}
```

---

### PUT /auth/profile

Update user profile information.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "full_name": "John Updated Doe",
  "email": "newemail@example.com"
}
```

**Response** (200):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "newemail@example.com",
  "full_name": "John Updated Doe"
}
```

---

## Problem Discovery Endpoints

### POST /user-input/

Submit a problem description for analysis.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "problem_description": "Small businesses struggle with inventory management",
  "domain": "Retail",
  "region": "North America",
  "target_audience": "Small business owners"
}
```

**Response** (201):
```json
{
  "success": true,
  "input_id": "inp_abc123",
  "message": "Problem submitted successfully",
  "created_at": "2026-05-13T10:00:00Z"
}
```

---

### GET /user-inputs/

Get all problem submissions for the current user.

**Headers**: `Authorization: Bearer <token>`

**Response** (200):
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "input_id": "inp_abc123",
    "problem_description": "Small businesses struggle with inventory management",
    "status": "completed",
    "current_stage": "ranking",
    "created_at": "2026-05-13T10:00:00Z",
    "updated_at": "2026-05-13T10:15:00Z"
  }
]
```

---

### GET /user-inputs/{input_id}

Get details of a specific problem submission.

**Headers**: `Authorization: Bearer <token>`

**Parameters**:
- `input_id` (path): Input ID

**Response** (200):
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "input_id": "inp_abc123",
  "problem_description": "Small businesses struggle with inventory management",
  "domain": "Retail",
  "region": "North America",
  "target_audience": "Small business owners",
  "status": "completed",
  "current_stage": "ranking",
  "created_at": "2026-05-13T10:00:00Z",
  "updated_at": "2026-05-13T10:15:00Z"
}
```

---

### GET /processing-status/{input_id}

Get processing status for a problem submission.

**Headers**: `Authorization: Bearer <token>`

**Parameters**:
- `input_id` (path): Input ID

**Response** (200):
```json
{
  "input_id": "inp_abc123",
  "overall_status": "processing",
  "progress_percentage": 65,
  "current_stage": "clustering",
  "message": "Clustering posts into topics",
  "description": "Grouping similar discussions together",
  "animation": "clustering",
  "next_action": "Extract pain points",
  "stages": {
    "keywords": { "status": "completed", "progress": 100 },
    "reddit": { "status": "completed", "progress": 100 },
    "embeddings": { "status": "completed", "progress": 100 },
    "filtering": { "status": "completed", "progress": 100 },
    "clustering": { "status": "processing", "progress": 65 },
    "pain_points": { "status": "pending", "progress": 0 },
    "ranking": { "status": "pending", "progress": 0 }
  },
  "estimated_time_remaining": "2 minutes",
  "can_view_results": false
}
```

---

### DELETE /user-inputs/{input_id}

Delete a problem submission.

**Headers**: `Authorization: Bearer <token>`

**Parameters**:
- `input_id` (path): Input ID

**Response** (200):
```json
{
  "success": true,
  "message": "Input deleted successfully"
}
```

---

## Idea Validation Endpoints

### POST /ideas/

Submit a new idea for validation.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "title": "AI-Powered Inventory Management",
  "description": "Smart inventory system for small businesses",
  "problem_statement": "Small businesses lose money due to poor inventory management",
  "solution_description": "AI system that predicts demand and optimizes stock levels",
  "target_market": "Small retail businesses with 1-50 employees",
  "business_model": "SaaS subscription",
  "team_capabilities": "Technical team with retail experience"
}
```

**Response** (201):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "AI-Powered Inventory Management",
  "description": "Smart inventory system for small businesses",
  "problem_statement": "Small businesses lose money due to poor inventory management",
  "solution_description": "AI system that predicts demand and optimizes stock levels",
  "target_market": "Small retail businesses with 1-50 employees",
  "business_model": "SaaS subscription",
  "team_capabilities": "Technical team with retail experience",
  "created_at": "2026-05-13T10:00:00Z",
  "updated_at": "2026-05-13T10:00:00Z"
}
```

---

### GET /ideas/

Get all ideas for the current user.

**Headers**: `Authorization: Bearer <token>`

**Query Parameters**:
- `sort_by` (optional): Field to sort by (e.g., "created_at", "title")
- `sort_order` (optional): "asc" or "desc"
- `min_score` (optional): Minimum validation score
- `max_score` (optional): Maximum validation score

**Response** (200):
```json
[
  {
    "id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "title": "AI-Powered Inventory Management",
    "description": "Smart inventory system for small businesses",
    "problem_statement": "Small businesses lose money due to poor inventory management",
    "solution_description": "AI system that predicts demand and optimizes stock levels",
    "target_market": "Small retail businesses with 1-50 employees",
    "created_at": "2026-05-13T10:00:00Z",
    "updated_at": "2026-05-13T10:00:00Z",
    "latest_validation": {
      "validation_id": "val_xyz789",
      "overall_score": 78,
      "status": "completed",
      "created_at": "2026-05-13T10:05:00Z"
    }
  }
]
```

---

### POST /validations/validate

Start validation process for an idea.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "idea_id": "507f1f77bcf86cd799439011",
  "config": {
    "includeWebSearch": true,
    "includeCompetitiveAnalysis": true,
    "maxCompetitorsToAnalyze": 5,
    "useCachedResults": false
  }
}
```

**Response** (201):
```json
{
  "validation_id": "val_xyz789",
  "idea_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "status": "processing",
  "overall_score": null,
  "individual_scores": null,
  "report_data": null,
  "created_at": "2026-05-13T10:05:00Z",
  "completed_at": null,
  "error_message": null
}
```

---

### GET /validations/{validation_id}

Get validation results.

**Headers**: `Authorization: Bearer <token>`

**Parameters**:
- `validation_id` (path): Validation ID

**Response** (200):
```json
{
  "validation_id": "val_xyz789",
  "idea_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "status": "completed",
  "overall_score": 78,
  "individual_scores": {
    "market_size": 85,
    "competition": 70,
    "feasibility": 80,
    "team": 75,
    "innovation": 82
  },
  "report_data": {
    "summary": "Strong market opportunity with moderate competition...",
    "strengths": ["Large market size", "Innovative approach"],
    "weaknesses": ["Competitive market", "Team experience"],
    "recommendations": ["Focus on differentiation", "Build partnerships"]
  },
  "created_at": "2026-05-13T10:05:00Z",
  "completed_at": "2026-05-13T10:10:00Z",
  "error_message": null
}
```

---

## Competitor Intelligence Endpoints

### POST /products/

Submit a product for competitor analysis.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "product_name": "InventoryPro",
  "product_description": "AI-powered inventory management for small businesses",
  "key_features": [
    "Demand forecasting",
    "Auto-reordering",
    "Analytics dashboard"
  ]
}
```

**Response** (201):
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "product_name": "InventoryPro",
  "product_description": "AI-powered inventory management for small businesses",
  "key_features": [
    "Demand forecasting",
    "Auto-reordering",
    "Analytics dashboard"
  ],
  "created_at": "2026-05-13T10:00:00Z",
  "updated_at": "2026-05-13T10:00:00Z"
}
```

---

### POST /competitor-analysis/analyze

Start competitor analysis.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "name": "InventoryPro",
  "description": "AI-powered inventory management for small businesses",
  "features": [
    "Demand forecasting",
    "Auto-reordering",
    "Analytics dashboard"
  ],
  "pricing": "$49/month",
  "target_audience": "Small retail businesses"
}
```

**Response** (200):
```json
{
  "success": true,
  "analysis_id": "ana_abc123",
  "execution_time": 15.5,
  "product": {
    "name": "InventoryPro",
    "description": "AI-powered inventory management for small businesses",
    "features": ["Demand forecasting", "Auto-reordering", "Analytics dashboard"],
    "pricing": "$49/month"
  },
  "top_competitors": [
    {
      "name": "StockMaster",
      "description": "Inventory management solution",
      "url": "https://stockmaster.com",
      "features": ["Inventory tracking", "Reporting", "Integrations"],
      "pricing": "$39/month",
      "competitor_type": "direct",
      "similarity_score": 0.85
    }
  ],
  "feature_matrix": {
    "features": ["Demand forecasting", "Auto-reordering", "Analytics dashboard"],
    "products": [
      {
        "name": "InventoryPro",
        "is_user_product": true,
        "feature_support": {
          "Demand forecasting": true,
          "Auto-reordering": true,
          "Analytics dashboard": true
        }
      }
    ]
  }
}
```

---

## Customer Insights Endpoints

### POST /customer-insights/analyze

Start customer insights analysis.

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "startup_idea": "AI-powered inventory management for small businesses",
  "target_market": "Small retail businesses",
  "product_category": "SaaS"
}
```

**Response** (201):
```json
{
  "success": true,
  "analysis_id": "ci_abc123",
  "message": "Analysis started successfully",
  "created_at": "2026-05-13T10:00:00Z"
}
```

---

### GET /customer-insights/analysis/{analysis_id}

Get customer insights analysis results.

**Headers**: `Authorization: Bearer <token>`

**Parameters**:
- `analysis_id` (path): Analysis ID

**Response** (200):
```json
{
  "analysis_id": "ci_abc123",
  "status": "completed",
  "communities": [
    {
      "name": "r/smallbusiness",
      "platform": "Reddit",
      "members": 1500000,
      "relevance_score": 0.92,
      "engagement_level": "high"
    }
  ],
  "segments": [
    {
      "name": "Tech-Savvy Retailers",
      "size": "25%",
      "characteristics": ["Early adopters", "Value automation"],
      "pain_points": ["Manual processes", "Data accuracy"]
    }
  ],
  "insights": {
    "key_findings": ["Strong demand for automation", "Price sensitivity"],
    "recommendations": ["Focus on ROI messaging", "Offer free trial"]
  },
  "created_at": "2026-05-13T10:00:00Z",
  "completed_at": "2026-05-13T10:10:00Z"
}
```

---

## Rate Limiting

API rate limits (planned):
- **Authenticated requests**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1620000000
```

---

## Pagination

For endpoints that return lists, pagination is supported:

**Query Parameters**:
- `page` (default: 1): Page number
- `limit` (default: 20): Items per page

**Response Headers**:
```
X-Total-Count: 150
X-Page: 1
X-Per-Page: 20
X-Total-Pages: 8
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid credentials |
| `AUTH_002` | Token expired |
| `AUTH_003` | Token invalid |
| `VAL_001` | Validation failed |
| `VAL_002` | Invalid input format |
| `DB_001` | Database error |
| `EXT_001` | External API error |
| `SYS_001` | System error |

---

## Webhooks (Planned)

Webhooks will be available for:
- Validation completion
- Analysis completion
- Processing status updates

---

**Last Updated**: May 13, 2026
