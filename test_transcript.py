import asyncio
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.config import settings

async def test_transcript():
    adapter = YouTubeAPIAdapter(api_key=settings.youtube_api_key)
    
    # Test with a well-known video that usually has transcripts
    test_videos = [
        "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "jNQXAC9IVRw",  # Me at the zoo (first YouTube video)
        "9bZkp7q19f0",  # Gangnam Style
    ]
    
    print("🧪 Testing transcript functionality with known videos...")
    
    for video_id in test_videos:
        try:
            print(f"\n📺 Testing video: {video_id}")
            video = await adapter.get_video_details(video_id)
            print(f"✅ Title: {video.title}")
            
            transcript = await adapter.get_video_transcript(video_id)
            if transcript:
                print(f"✅ Transcript: {len(transcript)} characters")
                print(f"📄 Preview: {transcript[:100]}...")
            else:
                print("❌ No transcript available")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_transcript())