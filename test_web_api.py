#!/usr/bin/env python3
"""
Test script for the web API endpoints.
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000/api"
    
    print("🧪 Testing YouTube Playlist Reader Web API")
    print("=" * 50)
    
    # Test health check
    print("1. 🏥 Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data['status']}")
            print(f"   📺 YouTube API: {'✅' if data['youtube_api'] else '❌'}")
            print(f"   🤖 Ollama: {'✅' if data['ollama'] else '❌'}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test summary
    print("\n2. 📋 Testing playlist summary...")
    try:
        response = requests.get(f"{base_url}/summary")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Playlist: {data['title']}")
            print(f"   📺 Videos: {data['video_count']}")
            print(f"   📝 Summary length: {len(data['summary']['answer'])} chars")
        else:
            print(f"   ❌ Summary failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test question (JSON API)
    print("\n3. 🤖 Testing Q&A...")
    try:
        question_data = {
            "question": "What kind of games are in this playlist?",
            "max_videos": 5
        }
        response = requests.post(
            f"{base_url}/ask",
            data=question_data  # Form data for the endpoint
        )
        if response.status_code == 200:
            # Check if it's HTML (HTMX) or JSON
            if response.headers.get('content-type', '').startswith('text/html'):
                print(f"   ✅ Q&A HTML response: {len(response.text)} chars")
            else:
                data = response.json()
                print(f"   ✅ Answer: {data['answer'][:100]}...")
                print(f"   📊 Confidence: {data['confidence']:.1%}")
        else:
            print(f"   ❌ Q&A failed: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test video search
    print("\n4. 🔍 Testing video search...")
    try:
        search_data = {
            "query": "among us",
            "max_results": 3
        }
        response = requests.post(
            f"{base_url}/search",
            data=search_data
        )
        if response.status_code == 200:
            if response.headers.get('content-type', '').startswith('text/html'):
                print(f"   ✅ Search HTML response: {len(response.text)} chars")
            else:
                data = response.json()
                print(f"   ✅ Found {len(data)} videos")
                if data:
                    print(f"   📺 First result: {data[0]['title']}")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 API testing completed!")
    print("\n🌐 Access the web interface at: http://localhost:8000")

if __name__ == "__main__":
    test_api()