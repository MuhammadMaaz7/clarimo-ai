# Input Validation System

## Overview

Clarimo AI implements a comprehensive input validation system across all modules to prevent users from submitting gibberish, random text, or inappropriate content. This ensures high-quality data processing and meaningful results.

## Validation Architecture

### Two Validation Approaches

Clarimo AI uses two different validation strategies depending on the module:

#### Approach 1: Multi-Layer Validation (Problem Discovery)
Used for complex inputs that require detailed domain validation.

```
User Input
    ↓
┌─────────────────────────────────────┐
│  Layer 1: Basic Validation         │
│  - Length checks                    │
│  - Empty string detection           │
│  ⚡ Fast (< 1ms)                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Layer 2: Pattern Validation       │
│  - Domain pattern detection         │
│  - Keyboard mashing detection       │
│  ⚡ Fast (< 5ms)                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Layer 3: AI Validation             │
│  - Semantic understanding           │
│  - Domain legitimacy (STRICT)       │
│  ⏱️ Slower (1-3 seconds)            │
└─────────────────────────────────────┘
    ↓
✅ Input Accepted
```

#### Approach 2: Unified Relevance Checking (GTM, Launch Planning, Customer Insights)
Used for simpler inputs with consistent validation logic.

```
User Input
    ↓
┌─────────────────────────────────────┐
│  Pydantic Validation                │
│  - Field type checking              │
│  - Length constraints               │
│  - Required fields                  │
│  ⚡ Fast (< 1ms)                    │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Relevance Checker (AI)             │
│  - Business context validation      │
│  - Gibberish detection              │
│  - Non-business query rejection     │
│  ⏱️ Fast (0.5-1 second)             │
└─────────────────────────────────────┘
    ↓
✅ Input Accepted
```

## Module-Specific Validation

### 1. Problem Discovery Module

**Validation Type**: Multi-Layer (3 layers)

**Location**: `Backend/app/services/problem_discovery/keyword_generation_service.py`

**Why Multi-Layer**: Requires strict domain validation to prevent nonsensical domains like "HAFFUUU" or "qwerty123"

**Validation Layers**:
- Layer 1: Basic length and format checks
- Layer 2: Pattern-based domain validation (detects keyboard mashing, repeated characters)
- Layer 3: AI-powered semantic validation

**Example**:
```python
✅ Valid: "Small businesses struggle with inventory" + domain: "retail"
❌ Invalid: "Financial problems" + domain: "HAFFUUU" (random characters detected)
```

---

### 2. Idea Validation Module

**Validation Type**: Pydantic Only

**Location**: `Backend/app/db/models/idea_model.py`

**Why Pydantic Only**: Structured data with clear field requirements

**Validation**:
```python
class IdeaCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    problem_statement: str = Field(..., min_length=10, max_length=1000)
    solution_description: str = Field(..., min_length=10, max_length=2000)
    target_market: str = Field(..., min_length=5, max_length=500)
```

---

### 3. Competitor Intelligence Module

**Validation Type**: Pydantic Only

**Location**: `Backend/app/db/models/product_model.py`

**Why Pydantic Only**: Structured product data with clear requirements

**Validation**:
```python
class ProductAnalysisRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    features: List[str] = Field(..., min_items=1, max_items=20)
```

---

### 4. Customer Insights Module ✨ NEW

**Validation Type**: Unified Relevance Checking

**Location**: `Backend/app/api/customer_insights/routes_analysis.py`

**Why Relevance Checking**: Consistent with GTM and Launch Planning for similar input types

**Validation Process**:
```python
# Step 1: Pydantic validation (automatic)
startup_idea: str = Field(..., min_length=10, max_length=500)
target_market: Optional[str] = Field(None, max_length=200)

# Step 2: Relevance checking (AI-powered)
is_valid, reason = await relevance_checker.validate_relevance(
    input_text=validation_text,
    context_type="customer insights analysis"
)
```

**What It Rejects**:
- ❌ Random characters or gibberish (e.g., 'asdfghj', 'cscaskjcs')
- ❌ Non-business queries (e.g., 'what is the weather', 'tell me a joke')
- ❌ General information tasks (e.g., 'how to bake a cake')
- ❌ Unrelated queries (e.g., 'stock price of Apple')
- ❌ Personal requests or nonsense

**What It Accepts**:
- ✅ Vague but legitimate business ideas (e.g., 'Uber for laundry')
- ✅ Local physical businesses (e.g., 'Noodle shop', 'Barber shop')
- ✅ Hardware/IoT products (e.g., 'Smart collar for dogs')
- ✅ Market problems (e.g., 'people struggle to find parking')
- ✅ Technical product descriptions

**Example**:
```python
✅ Valid: "AI-powered meal planning app for busy professionals"
✅ Valid: "Noodle shop in my street"
❌ Invalid: "asdfghjkl" → "This appears to be gibberish"
❌ Invalid: "what is the weather" → "This is an unrelated general knowledge query"
```

---

### 5. Launch Planning Module

**Validation Type**: Unified Relevance Checking

**Location**: `Backend/app/api/launch_planning/routes_plan.py`

**Validation Process**:
```python
is_valid, reason = await relevance_checker.validate_relevance(
    input_text=request.idea_description,
    context_type="launch plan"
)
```

---

### 6. GTM Strategy Module

**Validation Type**: Unified Relevance Checking

**Location**: `Backend/app/api/gtm/routes_gtm.py`

**Validation Process**:
```python
is_valid, reason = await relevance_checker.validate_relevance(
    input_text=request.startup_description,
    context_type="Go-to-Market Strategy"
)
```

---

## Shared Relevance Checker

**Location**: `Backend/app/services/shared/relevance_checker.py`

**Used By**: Customer Insights, Launch Planning, GTM Strategy

**Features**:
- Ultra-fast validation using Groq LLM
- Fallback to OpenRouter if Groq fails
- Temperature: 0.0 (strict, consistent validation)
- Returns: `(is_relevant: bool, reason: str)`

**Implementation**:
```python
class RelevanceChecker:
    def __init__(self):
        self.llm = UnifiedLLMService(provider_order=["groq", "openrouter"])
        self.temperature = 0.0  # Strict validation
    
    async def validate_relevance(
        self, 
        input_text: str, 
        context_type: str = "startup idea"
    ) -> Tuple[bool, str]:
        # Validates if input is relevant to startup/product development
        # Returns (is_relevant, error_message)
```

---

## Validation Comparison Table

| Module | Validation Type | Layers | Speed | Strictness |
|--------|----------------|--------|-------|------------|
| **Problem Discovery** | Multi-Layer | 3 | 1-3s | Very Strict |
| **Idea Validation** | Pydantic Only | 1 | <1ms | Moderate |
| **Competitor Intelligence** | Pydantic Only | 1 | <1ms | Moderate |
| **Customer Insights** | Relevance Checker | 2 | 0.5-1s | Strict |
| **Launch Planning** | Relevance Checker | 2 | 0.5-1s | Strict |
| **GTM Strategy** | Relevance Checker | 2 | 0.5-1s | Strict |

---

## API Endpoints

### Customer Insights Validation
```http
POST /api/customer-insights/validate-input
Content-Type: application/json
Authorization: Bearer <token>

{
  "startup_idea": "AI meal planning app",
  "target_market": "Busy professionals"
}

Response:
{
  "success": true,
  "is_valid": true,
  "reason": "valid",
  "message": "Input is valid and ready for analysis"
}
```

### Problem Discovery Validation
```http
POST /api/problem-discovery/validate-input
Content-Type: application/json
Authorization: Bearer <token>

{
  "problemDescription": "Small businesses struggle with inventory",
  "domain": "retail"
}

Response:
{
  "success": true,
  "validation": {
    "is_valid": true,
    "reason": "Input describes a legitimate business problem",
    "confidence": 0.95
  }
}
```

---

## Performance Metrics

| Validation Type | Average Time | Success Rate | Fallback |
|-----------------|--------------|--------------|----------|
| Pydantic Only | < 1ms | 100% | N/A |
| Relevance Checker | 0.5-1s | 98%+ | Returns true on API failure |
| Multi-Layer | 1-3s | 95%+ | Rule-based validation |

---

## Error Handling

### Validation Failure (HTTP 400)
```json
{
  "detail": "This appears to be gibberish. Please provide a legitimate business description."
}
```

### API Failure (Graceful Degradation)
```python
# Relevance Checker: Returns true to avoid blocking users
return True, "Validation skipped."

# Multi-Layer: Falls back to rule-based validation
return {
  "is_valid": True,
  "reason": "Input passed pattern validation (AI validation unavailable)",
  "confidence": 0.6
}
```

---

## Best Practices

### For Users
1. **Be Specific**: Provide detailed business descriptions
2. **Use Real Words**: Avoid gibberish or test inputs
3. **Business Context**: Describe actual business problems or products
4. **Avoid Personal Info**: Don't include names, emails, or phone numbers

### For Developers
1. **Choose Right Validation**: Use Multi-Layer for complex inputs, Relevance Checker for simpler ones
2. **Fail Fast**: Reject obvious invalid inputs early
3. **Provide Feedback**: Give clear, actionable error messages
4. **Log Validation**: Track validation failures for improvement
5. **Test Thoroughly**: Test with various invalid inputs

---

## Conclusion

Clarimo AI uses a **two-tier validation strategy**:

1. **Multi-Layer Validation** (Problem Discovery): For inputs requiring strict domain validation
2. **Relevance Checking** (Customer Insights, GTM, Launch Planning): For consistent, fast validation of business descriptions

Both approaches ensure:
- ✅ **Quality**: Only meaningful inputs are processed
- ✅ **Speed**: Fast validation (0.5-3 seconds)
- ✅ **Consistency**: Similar modules use the same validation logic
- ✅ **Reliability**: Fallback mechanisms for high availability
- ✅ **User Experience**: Clear error messages and guidance

---

**Last Updated**: May 13, 2026
