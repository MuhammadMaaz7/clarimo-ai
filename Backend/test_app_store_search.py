"""
Test App Store and Play Store search functionality
"""

import asyncio
from app.services.module2_validation.external_data_service import get_external_data_service


async def test_app_store_search():
    """Test searching App Store and Play Store"""
    
    service = get_external_data_service()
    
    # Test keywords
    test_cases = [
        ["fitness", "workout", "training"],
        ["grocery", "shopping", "meal"],
        ["productivity", "task", "management"]
    ]
    
    for keywords in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing with keywords: {keywords}")
        print(f"{'='*60}\n")
        
        # Search all sources including app stores
        results = await service.search_similar_products(
            keywords=keywords,
            max_results=5,
            include_app_stores=True
        )
        
        # Display App Store results
        print(f"\n📱 APP STORE RESULTS ({results['app_store']['total_found']} found):")
        print("-" * 60)
        for app in results['app_store']['apps']:
            print(f"\n✓ {app['name']}")
            print(f"  Developer: {app['developer']}")
            print(f"  Rating: {app['rating']:.1f} ⭐ ({app['rating_count']:,} ratings)")
            print(f"  Price: ${app['price']}")
            print(f"  Category: {app['category']}")
            print(f"  URL: {app['url']}")
        
        # Display Play Store results
        print(f"\n\n🤖 PLAY STORE RESULTS ({results['play_store']['total_found']} found):")
        print("-" * 60)
        if 'error' in results['play_store']:
            print(f"  ⚠️  Error: {results['play_store']['error']}")
        else:
            for app in results['play_store']['apps']:
                print(f"\n✓ {app['name']}")
                print(f"  Developer: {app['developer']}")
                print(f"  Rating: {app['rating']:.1f} ⭐ ({app['rating_count']:,} ratings)")
                print(f"  Price: {'Free' if app['free'] else f'${app['price']}'}")
                print(f"  Category: {app['category']}")
                print(f"  Installs: {app['installs']}")
                print(f"  URL: {app['url']}")
        
        # Summary
        print(f"\n\n📊 SUMMARY:")
        print(f"  Total products found: {results['total_products_found']}")
        print(f"  - HackerNews: {len(results['hackernews']['products'])}")
        print(f"  - GitHub: {len(results['github']['repositories'])}")
        print(f"  - App Store: {len(results['app_store']['apps'])}")
        print(f"  - Play Store: {len(results['play_store']['apps'])}")


if __name__ == "__main__":
    print("🚀 Testing App Store and Play Store Search")
    print("=" * 60)
    asyncio.run(test_app_store_search())
    print("\n✅ Test completed!")
