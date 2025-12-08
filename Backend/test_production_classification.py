"""
Test production pipeline with classification
"""

import sys
import asyncio
sys.path.insert(0, 'Backend')

from app.services.module3_competitor_analysis.production_pipeline_service import ProductionPipelineService


async def test_production_pipeline():
    """Test the production pipeline with classification"""
    
    product_info = {
        "name": "TaskMaster Pro",
        "description": "AI-powered task management and productivity tool for teams with smart prioritization",
        "features": [
            "AI task prioritization",
            "Team collaboration",
            "Calendar integration",
            "Smart notifications"
        ],
        "pricing": "$9.99/month"
    }
    
    print("=" * 80)
    print("TESTING PRODUCTION PIPELINE WITH CLASSIFICATION")
    print("=" * 80)
    print(f"\nProduct: {product_info['name']}")
    print(f"Description: {product_info['description']}")
    print("\nRunning analysis...")
    print("-" * 80)
    
    # Run analysis
    result = await ProductionPipelineService.analyze_product(
        product_info=product_info,
        save_to_db=False
    )
    
    if not result.get('success'):
        print(f"\n❌ Analysis failed: {result.get('error')}")
        return
    
    print("\n✅ Analysis completed successfully!")
    print("=" * 80)
    
    # Check classification data
    print("\n📊 CLASSIFICATION DATA:")
    print("-" * 80)
    
    if 'market_insights' in result:
        insights = result['market_insights']
        print(f"Total Competitors: {insights.get('total_competitors', 0)}")
        print(f"Direct Competitors: {insights.get('direct_competitors', 0)}")
        print(f"Indirect Competitors: {insights.get('indirect_competitors', 0)}")
    else:
        print("❌ No market_insights in response")
    
    if 'classification_summary' in result:
        summary = result['classification_summary']
        print(f"\nClassification Summary:")
        print(f"  - Total: {summary.get('total', 0)}")
        print(f"  - Direct: {summary.get('direct', 0)} ({summary.get('direct_percentage', 0)}%)")
        print(f"  - Indirect: {summary.get('indirect', 0)}")
        print(f"  - Avg Similarity (Direct): {summary.get('avg_similarity_direct', 0):.3f}")
        print(f"  - Avg Similarity (Indirect): {summary.get('avg_similarity_indirect', 0):.3f}")
    else:
        print("❌ No classification_summary in response")
    
    print("\n" + "=" * 80)
    print("🏆 TOP COMPETITORS WITH CLASSIFICATION:")
    print("=" * 80)
    
    for i, comp in enumerate(result.get('top_competitors', []), 1):
        comp_type = comp.get('competitor_type', 'unknown')
        similarity = comp.get('similarity_score', 0)
        
        icon = "🔴" if comp_type == 'direct' else "🟡" if comp_type == 'indirect' else "⚪"
        
        print(f"\n{i}. {icon} {comp['name']}")
        print(f"   Type: {comp_type.upper() if comp_type else 'NOT CLASSIFIED'}")
        print(f"   Similarity: {similarity * 100:.1f}%" if similarity else "   Similarity: N/A")
        print(f"   Source: {comp.get('source', 'unknown')}")
        print(f"   Description: {comp.get('description', 'N/A')[:80]}...")
    
    print("\n" + "=" * 80)
    
    # Verify classification is present
    has_classification = all(
        comp.get('competitor_type') is not None 
        for comp in result.get('top_competitors', [])
    )
    
    if has_classification:
        print("✅ ALL COMPETITORS HAVE CLASSIFICATION DATA")
    else:
        print("❌ SOME COMPETITORS MISSING CLASSIFICATION DATA")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_production_pipeline())
