"""
Quick API Test - Verify Production Endpoint Works
Run this to test the competitor analysis API
"""

import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000/api/competitor-analysis/analyze"

# Test data - Simple task management product
test_product = {
    "name": "QuickTask",
    "description": "Lightning-fast task manager for busy professionals who need to get things done quickly",
    "features": [
        "Quick task entry",
        "Smart reminders",
        "Priority sorting",
        "Daily planning"
    ],
    "pricing": "$8/month",
    "target_audience": "Busy professionals and freelancers"
}

print("="*80)
print("🧪 TESTING COMPETITOR ANALYSIS API")
print("="*80)
print(f"\n📦 Product: {test_product['name']}")
print(f"   {test_product['description']}")
print(f"\n🔗 Endpoint: {API_URL}")
print("\n⏳ Starting analysis... (this will take 60-90 seconds)")
print("-"*80)

start_time = time.time()

try:
    # Make API request
    response = requests.post(
        API_URL,
        json=test_product,
        headers={"Content-Type": "application/json"},
        timeout=120  # 2 minutes timeout
    )
    
    execution_time = time.time() - start_time
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ SUCCESS! Analysis completed in {execution_time:.1f}s")
        print("="*80)
        
        # Display key results
        print(f"\n📊 RESULTS:")
        print(f"   Analysis ID: {result['analysis_id']}")
        print(f"   Execution Time: {result['execution_time']:.1f}s")
        print(f"   Total Competitors: {result['metadata']['total_competitors_analyzed']}")
        
        print(f"\n🏆 TOP COMPETITORS:")
        for i, comp in enumerate(result['top_competitors'][:3], 1):
            print(f"   {i}. {comp['name']}")
            print(f"      Source: {comp['source']}")
            print(f"      URL: {comp['url'][:60]}...")
            if comp.get('pricing'):
                print(f"      Pricing: {comp['pricing']}")
            print()
        
        print(f"🎯 MARKET OPPORTUNITIES:")
        for i, opp in enumerate(result['gap_analysis']['opportunities'][:3], 1):
            print(f"   {i}. {opp[:80]}...")
        
        print(f"\n⚡ UNIQUE STRENGTHS:")
        for i, strength in enumerate(result['gap_analysis']['unique_strengths'][:3], 1):
            print(f"   {i}. {strength[:80]}...")
        
        print(f"\n💡 MARKET POSITION:")
        print(f"   {result['insights']['market_position'][:150]}...")
        
        print("\n" + "="*80)
        print("✅ API TEST PASSED - System is working!")
        print("="*80)
        
        # Save full response
        with open('test_api_response.json', 'w') as f:
            json.dump(result, f, indent=2)
        print("\n💾 Full response saved to: test_api_response.json")
        
    else:
        print(f"\n❌ ERROR: API returned status {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.Timeout:
    print(f"\n⏱️ TIMEOUT: Analysis took longer than 120 seconds")
    print("   This might happen on first run. Try again.")
    
except requests.exceptions.ConnectionError:
    print(f"\n❌ CONNECTION ERROR: Cannot connect to {API_URL}")
    print("   Make sure the backend is running:")
    print("   cd Backend && python run.py")
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
