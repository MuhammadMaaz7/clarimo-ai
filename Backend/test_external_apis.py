"""
Test script for external APIs (HackerNews and GitHub)
Run this to verify APIs are working before testing full validation pipeline
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.module2_validation.external_data_service import ExternalDataService


async def test_hackernews_api():
    """Test HackerNews API"""
    print("\n" + "="*60)
    print("TEST 1: HackerNews API")
    print("="*60)
    
    service = ExternalDataService()
    
    # Test with simple keywords
    keywords = ["finance", "app"]
    print(f"\nSearching HackerNews for: {keywords}")
    
    try:
        result = await service._search_hackernews(keywords, max_results=5)
        
        print(f"\n✅ HackerNews API Response:")
        print(f"   Total found: {result.get('total_found', 0)}")
        print(f"   Products returned: {len(result.get('products', []))}")
        
        if result.get('products'):
            print(f"\n   Top 3 Products:")
            for i, product in enumerate(result['products'][:3], 1):
                print(f"\n   {i}. {product['title']}")
                print(f"      Points: {product['points']}, Comments: {product['num_comments']}")
                print(f"      URL: {product['url']}")
                if product.get('story_text'):
                    print(f"      Description: {product['story_text'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ HackerNews API FAILED: {str(e)}")
        return False


async def test_github_api():
    """Test GitHub API"""
    print("\n" + "="*60)
    print("TEST 2: GitHub API")
    print("="*60)
    
    service = ExternalDataService()
    
    # Test with simple keywords
    keywords = ["finance", "tracker"]
    print(f"\nSearching GitHub for: {keywords}")
    
    try:
        result = await service._search_github(keywords, max_results=5)
        
        print(f"\n✅ GitHub API Response:")
        print(f"   Total found: {result.get('total_found', 0)}")
        print(f"   Repositories returned: {len(result.get('repositories', []))}")
        
        if result.get('repositories'):
            print(f"\n   Top 3 Repositories:")
            for i, repo in enumerate(result['repositories'][:3], 1):
                print(f"\n   {i}. {repo['name']}")
                print(f"      Stars: {repo['stars']}, Forks: {repo['forks']}")
                print(f"      Language: {repo['language']}")
                print(f"      URL: {repo['url']}")
                if repo.get('description'):
                    print(f"      Description: {repo['description'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ GitHub API FAILED: {str(e)}")
        return False


async def test_combined_search():
    """Test combined search (both APIs)"""
    print("\n" + "="*60)
    print("TEST 3: Combined Search (HackerNews + GitHub)")
    print("="*60)
    
    service = ExternalDataService()
    
    # Test with realistic keywords
    keywords = ["personal", "finance", "budget"]
    print(f"\nSearching both APIs for: {keywords}")
    
    try:
        result = await service.search_similar_products(keywords, max_results=5)
        
        print(f"\n✅ Combined Search Response:")
        print(f"   Total products found: {result.get('total_products_found', 0)}")
        print(f"   HackerNews products: {len(result.get('hackernews', {}).get('products', []))}")
        print(f"   GitHub repositories: {len(result.get('github', {}).get('repositories', []))}")
        print(f"   Search keywords used: {result.get('search_keywords', [])}")
        
        # Show sample from each source
        hn_products = result.get('hackernews', {}).get('products', [])
        if hn_products:
            print(f"\n   Sample HackerNews Product:")
            p = hn_products[0]
            print(f"   - {p['title']} ({p['points']} points)")
        
        gh_repos = result.get('github', {}).get('repositories', [])
        if gh_repos:
            print(f"\n   Sample GitHub Repository:")
            r = gh_repos[0]
            print(f"   - {r['name']} ({r['stars']} stars)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Combined Search FAILED: {str(e)}")
        return False


async def test_keyword_extraction():
    """Test keyword extraction from idea"""
    print("\n" + "="*60)
    print("TEST 4: Keyword Extraction")
    print("="*60)
    
    service = ExternalDataService()
    
    # Test with sample idea
    title = "AI-Powered Personal Finance Assistant"
    problem = "Most people struggle to manage their finances effectively and lack personalized insights"
    solution = "A mobile app that uses AI to analyze spending patterns and provide personalized budgeting advice"
    market = "Young professionals aged 25-40"
    
    print(f"\nExtracting keywords from:")
    print(f"   Title: {title}")
    print(f"   Problem: {problem[:60]}...")
    print(f"   Solution: {solution[:60]}...")
    
    try:
        keywords = service.extract_keywords_from_idea(title, problem, solution, market)
        
        print(f"\n✅ Extracted Keywords: {keywords}")
        print(f"   Total keywords: {len(keywords)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Keyword Extraction FAILED: {str(e)}")
        return False


async def test_realistic_scenario():
    """Test with a realistic startup idea"""
    print("\n" + "="*60)
    print("TEST 5: Realistic Scenario - Full Search")
    print("="*60)
    
    service = ExternalDataService()
    
    # Realistic startup idea
    title = "Smart Water Bottle with Hydration Tracking"
    problem = "People forget to stay hydrated during workouts and daily activities"
    solution = "IoT-enabled water bottle that tracks consumption and sends reminders"
    market = "Fitness enthusiasts and athletes"
    
    print(f"\nTesting with idea: {title}")
    
    try:
        # Extract keywords
        keywords = service.extract_keywords_from_idea(title, problem, solution, market)
        print(f"\n   Keywords extracted: {keywords}")
        
        # Search for similar products
        result = await service.search_similar_products(keywords, max_results=5)
        
        print(f"\n✅ Search Results:")
        print(f"   Total competitors found: {result.get('total_products_found', 0)}")
        
        hn_products = result.get('hackernews', {}).get('products', [])
        gh_repos = result.get('github', {}).get('repositories', [])
        
        if hn_products:
            print(f"\n   HackerNews Products ({len(hn_products)}):")
            for i, p in enumerate(hn_products[:3], 1):
                print(f"   {i}. {p['title']} - {p['points']} points")
        
        if gh_repos:
            print(f"\n   GitHub Projects ({len(gh_repos)}):")
            for i, r in enumerate(gh_repos[:3], 1):
                print(f"   {i}. {r['name']} - {r['stars']} stars")
        
        if not hn_products and not gh_repos:
            print(f"\n   No competitors found - could be untapped market!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Realistic Scenario FAILED: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("EXTERNAL API TESTING SUITE")
    print("Testing HackerNews and GitHub APIs")
    print("="*60)
    
    results = []
    
    # Run all tests
    results.append(("HackerNews API", await test_hackernews_api()))
    results.append(("GitHub API", await test_github_api()))
    results.append(("Combined Search", await test_combined_search()))
    results.append(("Keyword Extraction", await test_keyword_extraction()))
    results.append(("Realistic Scenario", await test_realistic_scenario()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! APIs are working correctly.")
        print("You can now test the full validation pipeline.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("Fix the issues before testing the full pipeline.")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
