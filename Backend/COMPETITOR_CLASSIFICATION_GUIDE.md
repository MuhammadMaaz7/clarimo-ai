# Competitor Classification Guide

## Overview

The competitor classification system automatically categorizes each competitor as **Direct** or **Indirect** based on similarity to your product.

## How It Works

### Classification Algorithm

The system uses a multi-factor scoring approach:

1. **Text Similarity (Primary Factor)** - 70% weight
   - Uses TF-IDF vectorization and cosine similarity
   - Compares product name, description, and features
   - Product name is weighted 3x for importance

2. **Feature Overlap Bonus** - Up to 15% boost
   - Calculates Jaccard similarity between feature sets
   - More shared features = higher similarity

3. **Topic/Category Overlap Bonus** - Up to 10% boost
   - Checks if competitor topics appear in your product description
   - Helps identify competitors in the same category

### Classification Thresholds

```python
DIRECT_THRESHOLD = 0.25      # Similarity >= 0.25 = Direct Competitor
INDIRECT_THRESHOLD = 0.10    # Similarity >= 0.10 = Indirect Competitor
```

**Direct Competitors:**
- Similarity score ≥ 0.25
- Solve the same problem in a similar way
- Target the same audience
- Have significant feature overlap

**Indirect Competitors:**
- Similarity score 0.10 - 0.24
- Solve related problems differently
- May target different segments
- Partial feature overlap

## Implementation

### 1. Model Changes

Added to `Competitor` model:
```python
competitor_type: Optional[Literal['direct', 'indirect']] = None
similarity_score: Optional[float] = None
```

Added to `MarketInsights` model:
```python
direct_competitors: Optional[int] = None
indirect_competitors: Optional[int] = None
```

### 2. New Service

Created `competitor_classifier.py` with:
- `classify_competitors()` - Main classification function
- `get_classification_summary()` - Get statistics

### 3. Integration

Automatically runs during competitor analysis in `analysis_service.py`:
```python
all_competitors = CompetitorClassifier.classify_competitors(
    product_info={...},
    competitors=all_competitors
)
```

## API Response

### Competitor Object
```json
{
  "name": "Todoist",
  "description": "Task management app",
  "source": "web",
  "competitor_type": "direct",
  "similarity_score": 0.255,
  "features": [...],
  ...
}
```

### Market Insights
```json
{
  "total_competitors": 15,
  "direct_competitors": 5,
  "indirect_competitors": 10,
  "market_saturation": "medium",
  ...
}
```

### Classification Summary
```json
{
  "total": 15,
  "direct": 5,
  "indirect": 10,
  "direct_percentage": 33.3,
  "avg_similarity_direct": 0.342,
  "avg_similarity_indirect": 0.156,
  "top_direct_competitors": [
    {
      "name": "Todoist",
      "similarity": 0.425,
      "source": "web"
    }
  ]
}
```

## Customization

### Adjust Thresholds

Edit `competitor_classifier.py`:

```python
# More strict (fewer direct competitors)
DIRECT_THRESHOLD = 0.35
INDIRECT_THRESHOLD = 0.15

# More lenient (more direct competitors)
DIRECT_THRESHOLD = 0.20
INDIRECT_THRESHOLD = 0.08
```

### Adjust Weights

Modify bonuses in `competitor_classifier.py`:

```python
# Increase feature overlap importance
feature_bonus = jaccard * 0.20  # Default: 0.15

# Increase topic overlap importance
topic_bonus = overlap_ratio * 0.15  # Default: 0.10
```

### Add Custom Factors

Add new classification factors:

```python
@staticmethod
def _calculate_pricing_similarity(product_info, competitor) -> float:
    """Add pricing similarity bonus"""
    # Your logic here
    return bonus

# Then add to classify_competitors():
pricing_bonus = CompetitorClassifier._calculate_pricing_similarity(
    product_info, competitor
)
adjusted_score = similarity_score + feature_bonus + topic_bonus + pricing_bonus
```

## Testing

Run the test script:
```bash
python Backend/test_competitor_classification.py
```

Or test with your own data:
```python
from app.services.module3_competitor_analysis.competitor_classifier import CompetitorClassifier

product_info = {
    "product_name": "Your Product",
    "product_description": "Description...",
    "key_features": ["Feature 1", "Feature 2"]
}

competitors = [...]  # Your competitor data

classified = CompetitorClassifier.classify_competitors(
    product_info, 
    competitors
)

summary = CompetitorClassifier.get_classification_summary(classified)
print(summary)
```

## Frontend Integration

### Filter by Type

```javascript
// Get only direct competitors
const directCompetitors = competitors.filter(
  c => c.competitor_type === 'direct'
);

// Get only indirect competitors
const indirectCompetitors = competitors.filter(
  c => c.competitor_type === 'indirect'
);
```

### Display Classification

```javascript
// Show badge
<span className={`badge ${
  competitor.competitor_type === 'direct' 
    ? 'badge-danger' 
    : 'badge-warning'
}`}>
  {competitor.competitor_type}
</span>

// Show similarity score
<div>Similarity: {(competitor.similarity_score * 100).toFixed(1)}%</div>
```

### Sort by Similarity

```javascript
// Sort direct competitors by similarity
const sortedDirect = directCompetitors.sort(
  (a, b) => b.similarity_score - a.similarity_score
);
```

## Use Cases

### 1. Prioritize Analysis
Focus detailed analysis on direct competitors first

### 2. Market Positioning
- Direct competitors: Differentiate clearly
- Indirect competitors: Potential partnerships or expansion

### 3. Feature Planning
Analyze features of direct competitors more closely

### 4. Pricing Strategy
Compare pricing primarily with direct competitors

### 5. Marketing
- Direct: Head-to-head comparison
- Indirect: Complementary positioning

## Troubleshooting

### All Competitors Classified as Indirect
- **Cause:** Thresholds too high or product description too generic
- **Fix:** Lower `DIRECT_THRESHOLD` or improve product description detail

### Too Many Direct Competitors
- **Cause:** Thresholds too low or very saturated market
- **Fix:** Raise `DIRECT_THRESHOLD` to be more selective

### Low Similarity Scores
- **Cause:** Insufficient text data or very unique product
- **Fix:** Ensure competitors have descriptions and features populated

### Incorrect Classifications
- **Cause:** Missing feature/topic data
- **Fix:** Improve web scraping to get more competitor details

## Future Enhancements

Potential improvements:
1. **Machine Learning Model** - Train on labeled data
2. **User Feedback** - Allow manual reclassification
3. **Market Segment Detection** - Auto-detect market segments
4. **Competitive Intensity Score** - Rate threat level per competitor
5. **Time-based Tracking** - Track classification changes over time
