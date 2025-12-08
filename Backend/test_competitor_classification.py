"""
Test script for competitor classification
"""

import sys
sys.path.insert(0, 'Backend')

from app.services.module3_competitor_analysis.competitor_classifier import CompetitorClassifier


def test_classification():
    """Test the competitor classification logic"""
    
    # Sample product
    product_info = {
        "product_name": "TaskMaster Pro",
        "product_description": "AI-powered task management and productivity tool for teams",
        "key_features": [
            "AI task prioritization",
            "Team collaboration",
            "Calendar integration",
            "Smart notifications"
        ]
    }
    
    # Sample competitors
    competitors = [
        {
            "name": "Todoist",
            "description": "Task management and to-do list app with team features",
            "source": "web",
            "features": ["Task lists", "Team collaboration", "Calendar sync", "Reminders"],
            "topics": ["productivity", "task management"]
        },
        {
            "name": "Slack",
            "description": "Team communication and messaging platform",
            "source": "web",
            "features": ["Team chat", "File sharing", "Integrations"],
            "topics": ["communication", "collaboration"]
        },
        {
            "name": "Asana",
            "description": "Project and task management software for teams",
            "source": "web",
            "features": ["Project tracking", "Task management", "Team collaboration", "Timeline view"],
            "topics": ["project management", "productivity"]
        },
        {
            "name": "Google Calendar",
            "description": "Calendar and scheduling application",
            "source": "web",
            "features": ["Calendar", "Event scheduling", "Reminders"],
            "topics": ["calendar", "scheduling"]
        },
        {
            "name": "Notion",
            "description": "All-in-one workspace for notes, docs, and project management",
            "source": "web",
            "features": ["Notes", "Databases", "Task lists", "Team collaboration"],
            "topics": ["productivity", "workspace"]
        }
    ]
    
    # Classify competitors
    print("=" * 60)
    print("COMPETITOR CLASSIFICATION TEST")
    print("=" * 60)
    print(f"\nProduct: {product_info['product_name']}")
    print(f"Description: {product_info['product_description']}")
    print(f"Features: {', '.join(product_info['key_features'])}")
    print("\n" + "=" * 60)
    
    classified = CompetitorClassifier.classify_competitors(product_info, competitors)
    
    # Display results
    print("\nCLASSIFICATION RESULTS:")
    print("-" * 60)
    
    direct = [c for c in classified if c['competitor_type'] == 'direct']
    indirect = [c for c in classified if c['competitor_type'] == 'indirect']
    
    print(f"\n✓ DIRECT COMPETITORS ({len(direct)}):")
    for comp in sorted(direct, key=lambda x: x['similarity_score'], reverse=True):
        print(f"  • {comp['name']:<20} (Similarity: {comp['similarity_score']:.3f})")
        print(f"    {comp['description'][:70]}...")
    
    print(f"\n○ INDIRECT COMPETITORS ({len(indirect)}):")
    for comp in sorted(indirect, key=lambda x: x['similarity_score'], reverse=True):
        print(f"  • {comp['name']:<20} (Similarity: {comp['similarity_score']:.3f})")
        print(f"    {comp['description'][:70]}...")
    
    # Get summary
    summary = CompetitorClassifier.get_classification_summary(classified)
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("-" * 60)
    print(f"Total Competitors: {summary['total']}")
    print(f"Direct: {summary['direct']} ({summary['direct_percentage']}%)")
    print(f"Indirect: {summary['indirect']}")
    print(f"Avg Similarity (Direct): {summary['avg_similarity_direct']:.3f}")
    print(f"Avg Similarity (Indirect): {summary['avg_similarity_indirect']:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    test_classification()
