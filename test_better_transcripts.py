import asyncio
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.config import settings

async def test_better_transcripts():
    adapter = YouTubeAPIAdapter(api_key=settings.youtube_api_key)
    
    # Test with educational/tech videos that typically have captions
    test_videos = [
        "ZePiZzwF5RM",  # TED-Ed video (usually has captions)
        "kqQNkLwsA6Y",  # Khan Academy style video
        "9bZkp7q19f0",  # Gangnam Style (popular, likely has captions)
        "YQHsXMglC9A",  # Adele - Hello (music videos often have captions)
        "fJ9rUzIMcZQ",  # Queen - Bohemian Rhapsody (classic with captions)
    ]
    
    print("🧪 Testing improved transcript extraction...")
    
    for video_id in test_videos:
        try:
            print(f"\n📺 Testing video: {video_id}")
            
            # Get video details first
            video = await adapter.get_video_details(video_id)
            print(f"   🎥 Title: {video.title}")
            
            # Try to get transcript
            transcript = await adapter.get_video_transcript(video_id)
            if transcript:
                print(f"   ✅ SUCCESS! Transcript: {len(transcript)} characters")
                print(f"   📄 Preview: {transcript[:150]}...")
                break  # Stop at first successful transcript
            else:
                print("   ❌ No transcript available")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Also test with our original playlist videos to see if any have transcripts
    print(f"\n🎮 Testing your SIDEMEN playlist videos...")
    videos = await adapter.get_playlist_videos(str(settings.youtube_playlist_url), max_results=10)
    
    found_transcript = False
    for video in videos:
        transcript = await adapter.get_video_transcript(video.video_id)
        if transcript:
            print(f"   ✅ Found transcript in: {video.title}")
            print(f"   📄 Length: {len(transcript)} characters")
            print(f"   📄 Preview: {transcript[:150]}...")
            found_transcript = True
            break
    
    if not found_transcript:
        print("   ℹ️  No transcripts found in first 10 SIDEMEN videos")
        print("   💡 This is normal for gaming content - creators often disable captions")

if __name__ == "__main__":
    asyncio.run(test_better_transcripts())