import asyncio
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.config import settings

async def test_final_transcript():
    adapter = YouTubeAPIAdapter(api_key=settings.youtube_api_key)
    
    print("🚀 Testing improved transcript extraction with yt-dlp fallback...")
    
    # Test with a single video that should have captions
    test_video = "9bZkp7q19f0"  # Gangnam Style
    
    print(f"\n📺 Testing video: {test_video}")
    
    try:
        # Get video details first
        video = await adapter.get_video_details(test_video)
        print(f"   🎥 Title: {video.title}")
        
        # Try to get transcript with our improved method
        transcript = await adapter.get_video_transcript(test_video)
        if transcript:
            print(f"   ✅ SUCCESS! Transcript: {len(transcript)} characters")
            print(f"   📄 Preview: {transcript[:200]}...")
        else:
            print("   ❌ Still no transcript available")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test with first video from our playlist
    print(f"\n🎮 Testing first SIDEMEN video...")
    videos = await adapter.get_playlist_videos(str(settings.youtube_playlist_url), max_results=1)
    
    if videos:
        video = videos[0]
        print(f"   🎥 Title: {video.title}")
        transcript = await adapter.get_video_transcript(video.video_id)
        if transcript:
            print(f"   ✅ SUCCESS! Transcript: {len(transcript)} characters")
            print(f"   📄 Preview: {transcript[:200]}...")
        else:
            print("   ❌ No transcript available")

if __name__ == "__main__":
    asyncio.run(test_final_transcript())