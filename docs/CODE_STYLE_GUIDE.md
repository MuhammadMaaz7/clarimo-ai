# Code Style Guide

This document outlines the coding standards and conventions for Clarimo AI.

## General Principles

1. **Readability**: Code is read more often than written
2. **Consistency**: Follow established patterns
3. **Simplicity**: Keep it simple and straightforward
4. **Documentation**: Comment complex logic
5. **Testing**: Write tests for new features

---

## Python (Backend) Style Guide

### PEP 8 Compliance

Follow [PEP 8](https://pep8.org/) style guide for Python code.

### Naming Conventions

```python
# Classes: PascalCase
class UserService:
    pass

# Functions and variables: snake_case
def get_user_by_id(user_id: str):
    user_name = "John Doe"
    return user_name

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_BASE_URL = "https://api.example.com"

# Private methods: _leading_underscore
def _internal_helper():
    pass
```

### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import List, Optional, Dict, Any

def process_data(
    data: List[Dict[str, Any]],
    filter_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process and filter data.
    
    Args:
        data: List of dictionaries to process
        filter_key: Optional key to filter by
        
    Returns:
        Processed and filtered data
    """
    # Implementation
    return filtered_data
```

### Docstrings

Use Google-style docstrings:

```python
def validate_idea(
    idea_id: str,
    config: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    Validate a startup idea using AI analysis.
    
    This function performs comprehensive validation across multiple
    criteria including market size, competition, and feasibility.
    
    Args:
        idea_id: Unique identifier for the idea
        config: Optional configuration for validation process
            - include_web_search: Whether to include web research
            - max_competitors: Maximum competitors to analyze
            
    Returns:
        ValidationResult object containing scores and recommendations
        
    Raises:
        ValueError: If idea_id is invalid
        APIError: If external API calls fail
        
    Example:
        >>> result = validate_idea("idea_123", {"include_web_search": True})
        >>> print(result.overall_score)
        78
    """
    # Implementation
    pass
```

### Imports

Organize imports in this order:

```python
# Standard library imports
import os
import sys
from datetime import datetime
from typing import List, Optional

# Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import numpy as np

# Local application imports
from app.core.config import settings
from app.db.database import get_database
from app.services.llm_service import get_llm_service
```

### Error Handling

```python
# Good: Specific exception handling
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data format: {e}")
    raise HTTPException(status_code=400, detail="Invalid data format")
except APIError as e:
    logger.error(f"External API error: {e}")
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")

# Bad: Catching all exceptions
try:
    result = process_data(data)
except Exception as e:
    pass  # Silent failure
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical issues")

# Include context in log messages
logger.info(f"Processing idea validation for idea_id={idea_id}")
logger.error(f"Failed to fetch data from {url}: {error_message}")
```

### Code Comments

```python
# Good: Explain WHY, not WHAT
# Use exponential backoff to avoid rate limiting
for attempt in range(MAX_RETRIES):
    try:
        response = api_call()
        break
    except RateLimitError:
        time.sleep(2 ** attempt)

# Bad: Stating the obvious
# Increment counter by 1
counter += 1
```

### Function Length

- Keep functions under 50 lines
- Extract complex logic into helper functions
- One function should do one thing

```python
# Good: Single responsibility
def validate_email(email: str) -> bool:
    """Validate email format."""
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

def validate_password(password: str) -> bool:
    """Validate password strength."""
    return len(password) >= 8 and any(c.isupper() for c in password)

# Bad: Multiple responsibilities
def validate_user_input(email: str, password: str, name: str) -> bool:
    # 100 lines of validation logic
    pass
```

---

## TypeScript (Frontend) Style Guide

### Naming Conventions

```typescript
// Interfaces and Types: PascalCase
interface UserProfile {
  id: string;
  email: string;
  fullName: string;
}

type ValidationStatus = 'pending' | 'processing' | 'completed' | 'failed';

// Functions and variables: camelCase
const getUserById = (userId: string): UserProfile => {
  const userName = "John Doe";
  return { id: userId, email: "", fullName: userName };
};

// Constants: UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const API_BASE_URL = "https://api.example.com";

// React Components: PascalCase
const UserDashboard: React.FC = () => {
  return <div>Dashboard</div>;
};

// Private functions: _leadingUnderscore (optional)
const _internalHelper = () => {
  // Internal use only
};
```

### Type Annotations

Always use TypeScript types:

```typescript
// Good: Explicit types
interface ValidationResult {
  overallScore: number;
  individualScores: {
    marketSize: number;
    competition: number;
    feasibility: number;
  };
  recommendations: string[];
}

const validateIdea = async (
  ideaId: string,
  config?: ValidationConfig
): Promise<ValidationResult> => {
  // Implementation
};

// Bad: Using 'any'
const validateIdea = async (ideaId: any, config: any): Promise<any> => {
  // Implementation
};
```

### React Components

```typescript
// Functional components with TypeScript
interface DashboardProps {
  userId: string;
  onRefresh?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ userId, onRefresh }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetchDashboardData(userId);
  }, [userId]);

  const fetchDashboardData = async (id: string): Promise<void> => {
    setLoading(true);
    try {
      const response = await api.dashboard.getData(id);
      setData(response);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  return (
    <div className="dashboard">
      {/* Component JSX */}
    </div>
  );
};

export default Dashboard;
```

### Custom Hooks

```typescript
// Custom hooks start with 'use'
const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async (): Promise<void> => {
    try {
      const currentUser = await api.auth.me();
      setUser(currentUser);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    const response = await api.auth.login(email, password);
    setUser(response.user);
    localStorage.setItem('auth_token', response.access_token);
  };

  const logout = (): void => {
    setUser(null);
    localStorage.removeItem('auth_token');
  };

  return { user, loading, login, logout };
};

export default useAuth;
```

### Error Handling

```typescript
// Good: Specific error handling
try {
  const result = await api.validateIdea(ideaId);
  setValidationResult(result);
} catch (error) {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      // Handle authentication error
      redirectToLogin();
    } else if (error.status === 400) {
      // Handle validation error
      showError(error.message);
    } else {
      // Handle other API errors
      showError('An error occurred. Please try again.');
    }
  } else {
    // Handle unexpected errors
    console.error('Unexpected error:', error);
    showError('An unexpected error occurred.');
  }
}
```

### Comments

```typescript
/**
 * Validates a startup idea using AI-powered analysis.
 * 
 * @param ideaId - Unique identifier for the idea
 * @param config - Optional configuration for validation
 * @returns Promise resolving to validation results
 * 
 * @example
 * ```typescript
 * const result = await validateIdea('idea_123', {
 *   includeWebSearch: true,
 *   maxCompetitors: 5
 * });
 * console.log(result.overallScore);
 * ```
 */
const validateIdea = async (
  ideaId: string,
  config?: ValidationConfig
): Promise<ValidationResult> => {
  // Implementation
};
```

---

## CSS/Tailwind Style Guide

### Class Organization

```tsx
// Good: Organized by category
<div className="
  // Layout
  flex flex-col items-center justify-center
  // Spacing
  p-6 gap-4
  // Sizing
  w-full max-w-4xl
  // Colors
  bg-white text-gray-900
  // Effects
  rounded-lg shadow-lg
  // Responsive
  md:flex-row md:p-8
">
  Content
</div>

// Bad: Random order
<div className="text-gray-900 flex p-6 rounded-lg w-full bg-white shadow-lg">
  Content
</div>
```

### Custom Classes

```css
/* Use semantic class names */
.dashboard-card {
  @apply bg-white rounded-lg shadow-md p-6;
}

.primary-button {
  @apply bg-primary text-white px-4 py-2 rounded-md hover:bg-primary/90;
}

/* Avoid presentational names */
.blue-box { /* Bad */
  @apply bg-blue-500;
}

.notification-card { /* Good */
  @apply bg-blue-500;
}
```

---

## Git Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(validation): add version comparison feature

Implement ability to compare validation results across
different versions of the same idea.

Closes #123
```

```
fix(auth): resolve token expiration issue

Fixed bug where expired tokens were not being properly
handled, causing users to remain logged in.

Fixes #456
```

```
docs(api): update API documentation

Added examples for new validation endpoints and
updated response schemas.
```

---

## File Organization

### Backend Structure

```
app/
├── api/                    # API routes
│   ├── __init__.py
│   ├── routes_auth.py     # Authentication routes
│   └── problem_discovery/ # Module routes
│       ├── __init__.py
│       └── routes_*.py
├── core/                   # Core functionality
│   ├── config.py          # Configuration
│   ├── security.py        # Security utilities
│   └── dependencies.py    # FastAPI dependencies
├── db/                     # Database layer
│   ├── database.py        # Connection
│   ├── models/            # Database models
│   └── schemas/           # Pydantic schemas
├── services/               # Business logic
│   ├── shared/            # Shared services
│   └── [module]/          # Module services
└── utils/                  # Utility functions
```

### Frontend Structure

```
src/
├── components/             # React components
│   ├── ui/                # Base UI components
│   ├── shared/            # Shared components
│   └── [module]/          # Module components
├── pages/                  # Page components
├── contexts/               # React contexts
├── hooks/                  # Custom hooks
├── lib/                    # Utilities
├── services/               # Business logic
└── types/                  # TypeScript types
```

---

## Code Review Checklist

### Before Submitting PR

- [ ] Code follows style guide
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No console.log or debug code
- [ ] No commented-out code
- [ ] Meaningful commit messages
- [ ] PR description is clear

### Reviewing Code

- [ ] Code is readable and maintainable
- [ ] Logic is correct
- [ ] Edge cases handled
- [ ] Error handling appropriate
- [ ] Performance considerations
- [ ] Security implications
- [ ] Tests are comprehensive

---

## Best Practices

### DRY (Don't Repeat Yourself)

```python
# Good: Reusable function
def format_date(date: datetime) -> str:
    return date.strftime("%Y-%m-%d %H:%M:%S")

formatted_created = format_date(created_at)
formatted_updated = format_date(updated_at)

# Bad: Repeated code
formatted_created = created_at.strftime("%Y-%m-%d %H:%M:%S")
formatted_updated = updated_at.strftime("%Y-%m-%d %H:%M:%S")
```

### KISS (Keep It Simple, Stupid)

```python
# Good: Simple and clear
def is_valid_email(email: str) -> bool:
    return '@' in email and '.' in email.split('@')[1]

# Bad: Overly complex
def is_valid_email(email: str) -> bool:
    import re
    pattern = r'^(?:[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&\'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-zA-Z0-9-]*[a-zA-Z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$'
    return bool(re.match(pattern, email))
```

### YAGNI (You Aren't Gonna Need It)

Don't add functionality until it's needed.

```python
# Good: Only what's needed now
class User:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

# Bad: Premature optimization
class User:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.preferences = {}  # Not needed yet
        self.settings = {}     # Not needed yet
        self.metadata = {}     # Not needed yet
```

---

**Last Updated**: May 13, 2026
