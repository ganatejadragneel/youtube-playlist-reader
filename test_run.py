import asyncio
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.config import settings

async def main():
    print("🚀 Testing YouTube Playlist Reader")
    print(f"📋 Playlist URL: {settings.youtube_playlist_url}")
    print(f"🔑 API Key: {'✅ Set' if settings.youtube_api_key else '❌ Not set'}")
    
    # Initialize adapter
    adapter = YouTubeAPIAdapter(api_key=settings.youtube_api_key)
    
    try:
        # Get playlist info
        print("\n📥 Fetching playlist metadata...")
        playlist = await adapter.get_playlist(str(settings.youtube_playlist_url))
        print(f"✅ Playlist: {playlist.title}")
        print(f"📺 Channel: {playlist.channel_title}")
        print(f"🎬 Videos: {playlist.video_count}")
        
        # Get first 3 videos
        print("\n📥 Fetching first 3 videos...")
        videos = await adapter.get_playlist_videos(str(settings.youtube_playlist_url), max_results=3)
        
        for i, video in enumerate(videos, 1):
            print(f"\n{i}. 🎥 {video.title}")
            print(f"   📅 Published: {video.published_at.strftime('%Y-%m-%d')}")
            
            # Try to get transcript
            print("   📝 Fetching transcript...")
            transcript = await adapter.get_video_transcript(video.video_id)
            if transcript:
                print(f"   ✅ Transcript: {len(transcript)} characters")
                print(f"   📄 Preview: {transcript[:150]}...")
            else:
                print("   ❌ No transcript available")
        
        print("\n🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("💡 Make sure Ollama is running and your playlist URL is valid")

if __name__ == "__main__":
    asyncio.run(main())