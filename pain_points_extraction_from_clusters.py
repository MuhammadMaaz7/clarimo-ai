import json
import time
import math
import os
from pathlib import Path
from groq import Groq

# ---------- CONFIG ----------
API_KEY = os.getenv("GROQ_API_KEY", "your-api-key-here")
MODEL = "llama-3.3-70b-versatile"
MAX_RESPONSE_TOKENS = 800
CONSERVATIVE_CHAR_PER_TOKEN = 4.0
MAX_CHARS_PER_CLUSTER = 4000
SAMPLE_POSTS_PER_CLUSTER = 4
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2.0

# ---------- HELPERS ----------
def est_tokens_from_chars(chars):
    """Conservative estimate: tokens ~= chars / 4"""
    return math.ceil(chars / CONSERVATIVE_CHAR_PER_TOKEN)

def safe_truncate(text, max_chars):
    """Safely truncate text to maximum characters, preserving sentence boundaries when possible."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    # try to cut at the last sentence boundary for nicer output
    cut = text[:max_chars]
    last_period = cut.rfind('.')
    last_exclamation = cut.rfind('!')
    last_question = cut.rfind('?')
    last_sentence_end = max(last_period, last_exclamation, last_question)
    
    if last_sentence_end > int(max_chars * 0.4):
        return cut[: last_sentence_end + 1] + " [TRUNCATED]"
    return cut + " [TRUNCATED]"

def extract_post_references(cluster, max_posts=5):
    """
    Extract structured post references from cluster data.
    Returns a list of posts with essential metadata for frontend display.
    """
    post_references = []
    
    # Get sample posts from cluster
    sample_posts = cluster.get("sample_posts", [])[:max_posts]
    
    for post in sample_posts:
        post_ref = {
            "post_id": post.get("post_id") or post.get("doc_id") or "unknown",
            "subreddit": post.get("subreddit", ""),
            "created_utc": post.get("created_utc", ""),
            "url": post.get("url", ""),
            "text": safe_truncate(post.get("text") or post.get("body") or "", 500),
            "title": post.get("title", ""),
            "score": post.get("score", 0),
            "num_comments": post.get("num_comments", 0)
        }
        # Clean up empty values
        post_ref = {k: v for k, v in post_ref.items() if v}
        post_references.append(post_ref)
    
    return post_references

def build_cluster_payload(cluster, posts_index):
    """
    Build a compact, human-readable block for a single cluster.
    Attach up to SAMPLE_POSTS_PER_CLUSTER sample posts from posts_index if available.
    """
    parts = []
    cid = cluster.get("cluster_id", cluster.get("id", "unknown"))
    parts.append(f"Cluster ID: {cid}")
    parts.append(f"Count: {cluster.get('count', '')}  Percentage: {cluster.get('percentage', '')}")
    
    # sample_texts
    sample_texts = cluster.get("sample_texts", [])
    if sample_texts:
        # Filter out empty texts and join with separator
        valid_texts = [t for t in sample_texts if t is not None and t.strip() != ""]
        if valid_texts:
            joined = " || ".join(valid_texts)
            joined = safe_truncate(joined, 800)
            parts.append("Sample Texts: " + joined)
    
    # sample_posts: try to get richer posts from cluster_posts index
    sample_posts = cluster.get("sample_posts", [])[:SAMPLE_POSTS_PER_CLUSTER]
    posts_strs = []
    for p in sample_posts:
        # If cluster_posts provided as a mapping, try to lookup more content by doc_id or post_id
        doc_id = p.get("doc_id") or p.get("post_id")
        url = p.get("url", "") or doc_id or ""
        subreddit = p.get("subreddit", "")
        created = p.get("created_utc", "")
        text_snip = p.get("text") or p.get("body") or ""
        text_snip = safe_truncate(text_snip, 300)
        posts_strs.append(f"[{subreddit}] {created} {url} // {text_snip}")
    
    if posts_strs:
        parts.append("Sample Posts:\n" + "\n".join(posts_strs))
    
    if "created_at" in cluster:
        parts.append(f"Cluster created_at: {cluster.get('created_at')}")
    
    block = "\n".join(parts)
    # enforce per-cluster limit
    if len(block) > MAX_CHARS_PER_CLUSTER:
        block = safe_truncate(block, MAX_CHARS_PER_CLUSTER)
    return block

def parse_llm_response(response_text, cluster_id, post_references):
    """
    Parse LLM response and structure it with post references.
    Returns a structured dictionary suitable for frontend display.
    """
    try:
        # Initialize structured response
        structured_response = {
            "cluster_id": cluster_id,
            "marketable_pain_point": "",
            "domain": "",
            "problem": "",
            "problem_scope": "",
            "potential_solution": "",
            "post_references": post_references,
            "analysis_timestamp": time.time(),
            "source": "reddit_cluster_analysis"
        }
        
        # Simple parsing of the LLM response
        lines = response_text.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('**Marketable Pain Point:**'):
                structured_response["marketable_pain_point"] = line.replace('**Marketable Pain Point:**', '').strip().strip('"')
            elif line.startswith('**Domain:**'):
                structured_response["domain"] = line.replace('**Domain:**', '').strip()
            elif line.startswith('**Problem:**'):
                structured_response["problem"] = line.replace('**Problem:**', '').strip()
            elif line.startswith('**Problem Scope:**'):
                structured_response["problem_scope"] = line.replace('**Problem Scope:**', '').strip()
            elif line.startswith('**Potential Solution:**'):
                structured_response["potential_solution"] = line.replace('**Potential Solution:**', '').strip()
        
        return structured_response
        
    except Exception as e:
        print(f"Error parsing LLM response for cluster {cluster_id}: {e}")
        # Return a basic structure even if parsing fails
        return {
            "cluster_id": cluster_id,
            "marketable_pain_point": "Analysis failed",
            "domain": "Unknown",
            "problem": "Failed to parse analysis",
            "problem_scope": "N/A",
            "potential_solution": "N/A",
            "post_references": post_references,
            "analysis_timestamp": time.time(),
            "source": "reddit_cluster_analysis",
            "error": str(e)
        }

def process_cluster_with_llm(client, cluster_id, cluster_block, post_references, max_response_tokens=MAX_RESPONSE_TOKENS):
    """Process a single cluster with the LLM and return structured response with post references."""
    
    prompt = f"""
You are a market analyst and domain researcher specializing in user behavior and product pain point discovery.

For the single Reddit discussion cluster below, rewrite and elaborate on it as a clearly defined PAIN POINT, including:
1) Marketable Pain Point Title (short, catchy)
2) Domain (industry/area)
3) Problem (what users are struggling with, why it's important)
4) Problem Scope (who is affected, where, under what circumstances — be specific)
5) Potential Solution (concise, realistic direction)

Output exactly in this format:

Cluster {cluster_id}
**Marketable Pain Point:** "..."
**Domain:** ...
**Problem:** ...
**Problem Scope:** ...
**Potential Solution:** ...

Cluster data:
{cluster_block}
"""

    # Token management
    prompt_chars = len(prompt)
    prompt_tokens_est = est_tokens_from_chars(prompt_chars)
    print(f" Prompt chars ~{prompt_chars}, est tokens ~{prompt_tokens_est}. Max response tokens: {max_response_tokens}")

    # If prompt seems too large in tokens, do an emergency truncation
    GROQ_TOKEN_LIMIT = 12000
    allowed_prompt_tokens = GROQ_TOKEN_LIMIT - max_response_tokens
    
    if prompt_tokens_est > allowed_prompt_tokens:
        print(" Prompt appears large. Truncating cluster content further to fit token budget.")
        reduction_factor = allowed_prompt_tokens / prompt_tokens_est
        new_max_chars = int(len(cluster_block) * reduction_factor * 0.9)  # 10% safety margin
        cluster_block = safe_truncate(cluster_block, new_max_chars)
        prompt = prompt.split("Cluster data:")[0] + "Cluster data:\n" + cluster_block
        prompt_chars = len(prompt)
        prompt_tokens_est = est_tokens_from_chars(prompt_chars)
        print(f" After truncation: prompt chars ~{prompt_chars}, est tokens ~{prompt_tokens_est}")

    # API call with retries
    for attempt in range(RETRY_ATTEMPTS):
        try:
            completion = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional market researcher. Be concise and analytical."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_completion_tokens=max_response_tokens
            )
            response_text = completion.choices[0].message.content
            print(f" Success: received {len(response_text)} chars response for cluster {cluster_id}")
            
            # Parse and structure the response with post references
            structured_response = parse_llm_response(response_text, cluster_id, post_references)
            return structured_response
            
        except Exception as e:
            print(f" Error on attempt {attempt + 1} for cluster {cluster_id}: {e}")
            if attempt < RETRY_ATTEMPTS - 1:
                wait = RETRY_BACKOFF_BASE ** (attempt + 1)
                print(f" Retrying in {wait:.0f}s...")
                time.sleep(wait)
            else:
                print(f" Failed after {RETRY_ATTEMPTS} attempts for cluster {cluster_id}.")
                raise e
    
    return None

# ---------- MAIN FUNCTION ----------
def analyze_pain_points(cluster_summary_path, cluster_posts_path=None, output_dir="."):
    """
    Main function to analyze pain points from cluster data.
    
    Args:
        cluster_summary_path (str): Path to cluster summary JSON file
        cluster_posts_path (str, optional): Path to cluster posts JSON file
        output_dir (str): Directory to save output files
    
    Returns:
        dict: Results and statistics with structured pain point data
    """
    
    # Validate inputs
    if not os.path.exists(cluster_summary_path):
        raise FileNotFoundError(f"Cluster summary file not found: {cluster_summary_path}")
    
    # Load cluster summary
    with open(cluster_summary_path, "r", encoding="utf-8") as f:
        cluster_summary = json.load(f)

    # Load cluster posts if available
    cluster_posts = {}
    if cluster_posts_path and os.path.exists(cluster_posts_path):
        try:
            with open(cluster_posts_path, "r", encoding="utf-8") as f:
                cluster_posts = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load cluster posts: {e}")
    else:
        print("Warning: cluster_posts.json not found or unreadable. Continuing without richer posts.")

    # Extract clusters
    clusters_dict = cluster_summary.get("clusters") or cluster_summary
    
    # Sort clusters numerically when possible
    cluster_items = []
    for key, cluster in clusters_dict.items():
        try:
            # Try to convert to int for numeric sorting
            numeric_key = int(key)
            cluster_items.append((numeric_key, cluster))
        except (ValueError, TypeError):
            cluster_items.append((key, cluster))
    
    cluster_items.sort(key=lambda x: x[0] if isinstance(x[0], (int, float)) else str(x[0]))

    # Initialize Groq client
    if API_KEY == "your-api-key-here":
        raise ValueError("Please set the GROQ_API_KEY environment variable or update the API_KEY in the script")
    
    client = Groq(api_key=API_KEY)

    # Prepare output files
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    aggregated_file = output_dir / "marketable_pain_points_all.json"
    individual_files = []
    
    # Store all pain points with references for frontend
    all_pain_points = {
        "metadata": {
            "total_clusters": len(cluster_items),
            "analysis_timestamp": time.time(),
            "version": "1.0",
            "source_files": {
                "cluster_summary": cluster_summary_path,
                "cluster_posts": cluster_posts_path
            }
        },
        "pain_points": []
    }

    results = {
        "total_clusters": len(cluster_items),
        "processed": 0,
        "failed": 0,
        "individual_files": [],
        "aggregated_file": str(aggregated_file),
        "pain_points_data": all_pain_points
    }

    # Process each cluster
    for key, cluster in cluster_items:
        cluster_id = cluster.get("cluster_id", key)
        print(f"\nProcessing cluster {cluster_id} (key={key}) ...")
        
        try:
            # Extract post references before processing
            post_references = extract_post_references(cluster)
            cluster_block = build_cluster_payload(cluster, cluster_posts)
            
            # Process with LLM
            structured_pain_point = process_cluster_with_llm(
                client, cluster_id, cluster_block, post_references
            )
            
            if structured_pain_point:
                # Save individual file as JSON
                out_file = output_dir / f"pain_point_cluster_{cluster_id}.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(structured_pain_point, f, indent=2, ensure_ascii=False)
                individual_files.append(str(out_file))
                
                # Add to aggregated pain points
                all_pain_points["pain_points"].append(structured_pain_point)
                
                results["processed"] += 1
                print(f"✓ Successfully processed cluster {cluster_id} with {len(post_references)} post references")
            else:
                results["failed"] += 1
                print(f"✗ Failed to process cluster {cluster_id}")
                
        except Exception as e:
            results["failed"] += 1
            print(f"✗ Error processing cluster {cluster_id}: {e}")
            
            # Create error entry with available post references
            error_entry = {
                "cluster_id": cluster_id,
                "marketable_pain_point": "Analysis Failed",
                "domain": "Error",
                "problem": f"Failed to analyze: {str(e)}",
                "problem_scope": "N/A",
                "potential_solution": "N/A",
                "post_references": extract_post_references(cluster),
                "analysis_timestamp": time.time(),
                "source": "reddit_cluster_analysis",
                "error": True,
                "error_message": str(e)
            }
            all_pain_points["pain_points"].append(error_entry)
        
        # Rate limiting delay
        time.sleep(0.6)

    # Save aggregated JSON file
    with open(aggregated_file, "w", encoding="utf-8") as f:
        json.dump(all_pain_points, f, indent=2, ensure_ascii=False)

    results["individual_files"] = individual_files
    
    print(f"\nAnalysis complete!")
    print(f"Total clusters: {results['total_clusters']}")
    print(f"Successfully processed: {results['processed']}")
    print(f"Failed: {results['failed']}")
    print(f"Aggregated results: {results['aggregated_file']}")
    print(f"Total pain points with post references: {len(all_pain_points['pain_points'])}")
    
    return results

# ---------- UTILITY FUNCTIONS FOR FRONTEND ----------
def load_pain_points_results(results_file_path):
    """Load pain points results for frontend display."""
    try:
        with open(results_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading pain points results: {e}")
        return None

def get_pain_points_by_domain(results_data):
    """Group pain points by domain for frontend categorization."""
    if not results_data or "pain_points" not in results_data:
        return {}
    
    by_domain = {}
    for pain_point in results_data["pain_points"]:
        domain = pain_point.get("domain", "Uncategorized")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(pain_point)
    
    return by_domain

# ---------- STANDALONE EXECUTION ----------
def main():
    """Standalone execution for testing."""
    
    # Update these paths for your environment
    summary_path = r"D:\FYP\Iteration 1\final pipeline\clarmio-ai-fyp\testting_clusters\cluster_summary.json"
    posts_path = r"D:\FYP\Iteration 1\final pipeline\clarmio-ai-fyp\testting_clusters\cluster_posts.json"
    output_dir = r"D:\FYP\Iteration 1\final pipeline\clarmio-ai-fyp\testting_clusters"
    
    try:
        results = analyze_pain_points(
            cluster_summary_path=summary_path,
            cluster_posts_path=posts_path,
            output_dir=output_dir
        )
        
        # Example of how frontend can use the data
        pain_points_data = load_pain_points_results(results["aggregated_file"])
        if pain_points_data:
            print(f"\nFrontend-ready data structure:")
            print(f"Total pain points: {len(pain_points_data['pain_points'])}")
            
            # Show first pain point with references as example
            if pain_points_data['pain_points']:
                first_point = pain_points_data['pain_points'][0]
                print(f"\nExample pain point:")
                print(f"Title: {first_point['marketable_pain_point']}")
                print(f"Domain: {first_point['domain']}")
                print(f"Post references: {len(first_point['post_references'])}")
                for i, post in enumerate(first_point['post_references'][:2], 1):
                    print(f"  Reference {i}: r/{post.get('subreddit', '')} - {post.get('text', '')[:100]}...")
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()