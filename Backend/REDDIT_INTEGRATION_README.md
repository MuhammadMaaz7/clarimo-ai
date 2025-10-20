# Reddit Integration System

This system automatically fetches Reddit posts based on AI-generated keywords from user inputs. The complete workflow is: **User Input** → **Keywords Generated** → **Reddit Posts Fetched** → **Saved to JSON Files**.

## Features

- **Automatic Integration**: Reddit posts fetched automatically after keyword generation
- **Dual Search Strategy**: Both search queries and subreddit-based extraction
- **Smart Query Generation**: Creates optimized search queries from keywords
- **File-Based Storage**: Raw Reddit data saved to JSON files (not database)
- **User Isolation**: Each user's data stored separately
- **Rate Limiting**: Respectful API usage with delays
- **Dry-Run Mode**: Works without Reddit API credentials for development

## Workflow

### Automatic Flow (Default)
1. **User submits problem discovery** via `/problems/discover`
2. **Keywords generated** using AI (subreddits, anchors, phrases)
3. **Reddit posts automatically fetched** using generated keywords
4. **Data saved** to JSON file in user-specific directory
5. **User gets response** with mock problem data + background fetching

### Manual Flow (Optional)
1. **User triggers manual fetch** via `/api/reddit/fetch/{input_id}`
2. **System uses existing keywords** for that input
3. **Reddit posts fetched** with custom parameters
4. **Data saved** to new JSON file

## API Endpoints

### Automatic Integration
- `POST /problems/discover` - Triggers automatic keyword generation + Reddit fetching

### Manual Reddit Operations
- `POST /api/reddit/fetch/{input_id}` - Manual Reddit fetch for specific input
- `GET /api/reddit/data/{input_id}` - Get Reddit data for input (summary or full)
- `GET /api/reddit/files/{input_id}` - List Reddit data files for input
- `GET /api/reddit/stats` - Get user's Reddit fetching statistics

## Configuration

### Reddit API Setup
1. **Create Reddit App**: Go to https://www.reddit.com/prefs/apps
2. **Choose "script" type** for personal use
3. **Get credentials**: client_id and client_secret
4. **Update .env file**:
   ```env
   REDDIT_CLIENT_ID=your_reddit_client_id_here
   REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
   REDDIT_USER_AGENT=RedditFetcher/1.0 by YourUsername
   ```

### Without Reddit API (Development)
- System automatically runs in **dry-run mode**
- No actual Reddit calls made
- Logs show `[DRY RUN]` messages
- File structure and workflow remain the same

## Data Structure

### File Organization
```
Backend/data/reddit_posts/
├── user_id_1/
│   ├── reddit_posts_input_1_20231019_143022.json
│   ├── reddit_posts_input_1_20231019_150315.json
│   └── reddit_posts_input_2_20231019_151200.json
├── user_id_2/
│   └── reddit_posts_input_3_20231019_152000.json
└── .gitkeep
```

### JSON File Structure
```json
{
  "user_id": "uuid-string",
  "input_id": "uuid-string", 
  "fetch_id": "uuid-string",
  "generated_at": "2023-10-19T14:30:22Z",
  "total_posts": 150,
  "status": "completed",
  "by_query": [
    {
      "query": "(\"AI tool\" OR automation) AND (\"too expensive\" OR \"hard to use\")",
      "domain_anchors_used": ["AI tool", "automation"],
      "problem_phrases_used": ["too expensive", "hard to use"],
      "posts": [
        {
          "id": "reddit_post_id",
          "title": "Post title",
          "content": "Post content",
          "url": "https://reddit.com/...",
          "subreddit": "startups",
          "created_utc": "2023-10-15T10:30:00Z",
          "score": 45,
          "num_comments": 12,
          "upvote_ratio": 0.89,
          "comments": []
        }
      ],
      "n_posts": 25
    }
  ],
  "by_subreddit": [
    {
      "subreddit": "startups",
      "meta": {
        "name": "startups",
        "exists": true,
        "accessible": true,
        "subscribers": 500000,
        "note": ""
      },
      "posts": [...],
      "extracted_count": 30
    }
  ]
}
```

## Search Strategy

### Query Generation
The system creates search queries by combining:
- **Domain Anchors**: Tools, technologies, workflows (from keywords)
- **Problem Phrases**: Pain points, frustrations (from keywords)
- **Format**: `(anchor1 OR anchor2) AND (problem1 OR problem2)`

### Example Queries
```
("AI tool" OR automation) AND ("too expensive" OR "hard to use")
(productivity OR workflow) AND ("time consuming" OR "manual work")
("SaaS" OR software) AND ("poor support" OR "confusing setup")
```

### Subreddit Extraction
- **Checks accessibility** of suggested subreddits
- **Fetches from multiple sources**: hot, top (year), new
- **Scores by engagement**: score + 2×comments
- **Filters low-quality** posts (score < 1, no comments)

## Performance & Limits

### Default Parameters
- **Queries per domain**: 6 (configurable)
- **Posts per query**: 50 (configurable)
- **Posts per subreddit**: 50 (configurable)
- **Rate limiting**: 0.5s between queries, 0.2s between subreddits

### Customizable Limits
```python
# Manual fetch with custom parameters
POST /api/reddit/fetch/{input_id}
{
  "queries_per_domain": 10,
  "per_query_limit": 100,
  "per_subreddit_limit": 100
}
```

## Error Handling

### Reddit API Issues
- **401 Unauthorized**: Invalid credentials → Dry-run mode
- **403 Forbidden**: Private subreddit → Skip with note
- **404 Not Found**: Subreddit doesn't exist → Skip with note
- **429 Rate Limited**: Too many requests → Automatic retry with delay
- **Network errors**: Connection issues → Retry with exponential backoff

### Graceful Degradation
- **Keyword generation fails** → No Reddit fetching
- **Reddit API unavailable** → Dry-run mode (no actual fetching)
- **Individual query fails** → Continue with other queries
- **Subreddit inaccessible** → Skip and continue with others
- **File save fails** → Error logged, but main request succeeds

## Monitoring & Logging

### Log Messages
```
INFO: Starting Reddit fetch for input abc123 (user: user456)
INFO: Generating search queries from keywords...
INFO: Executing query: ("AI tool" OR automation) AND ("too expensive")...
INFO: Found 25 posts
INFO: Checking r/startups...
INFO: Extracted 30 unique posts from r/startups
INFO: Reddit fetch completed: 75 from queries, 45 from subreddits, 120 total
INFO: Saved Reddit data to Backend/data/reddit_posts/user456/reddit_posts_abc123_20231019_143022.json
```

### Statistics Tracking
- **Total files** per user
- **Total posts** fetched
- **Total inputs** processed
- **Recent fetches** with timestamps and counts

## Integration Points

### With Keyword Generation
- **Automatic trigger** after successful keyword generation
- **Uses generated data**: subreddits, anchors, phrases
- **Respects keyword quality**: skips if insufficient keywords

### With User Input System
- **User isolation**: Each user's data separate
- **Input association**: Reddit data linked to specific inputs
- **Status tracking**: Success/failure logged

### With Frontend
- **Transparent operation**: Frontend gets normal response
- **Background processing**: Reddit fetching happens asynchronously
- **File-based access**: Frontend can request Reddit data via API

## Development & Testing

### Without Reddit API
```bash
# System automatically detects missing credentials
# Runs in dry-run mode with mock behavior
# All endpoints work, no actual Reddit calls
```

### With Reddit API
```bash
# Add credentials to .env
# System makes actual Reddit API calls
# Real data fetched and saved
```

### File Management
```bash
# Files automatically organized by user
# Old files preserved (no automatic cleanup)
# JSON format for easy inspection and processing
```

## Security & Privacy

### API Credentials
- **Environment variables only** (never in code)
- **User agent identification** for Reddit API compliance
- **Rate limiting respect** to avoid API abuse

### Data Storage
- **User isolation**: Each user's data in separate directory
- **No database storage**: Raw Reddit data kept in files only
- **Gitignore protection**: Data files not committed to repository

### Access Control
- **Authentication required**: All endpoints require valid user token
- **User-specific access**: Users can only access their own Reddit data
- **Input validation**: All parameters validated before processing

This system provides a robust, scalable solution for automatically fetching relevant Reddit posts based on user inputs and AI-generated keywords, with comprehensive error handling and user isolation.