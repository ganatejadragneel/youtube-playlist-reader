import asyncio
from src.adapters.youtube_adapter import YouTubeAPIAdapter
from src.adapters.ollama_adapter import OllamaAdapter
from src.services.qa_service import YouTubeQAService
from src.config import settings

async def demo_qa_system():
    print("🎬 YouTube Playlist Q&A System Demo")
    print("=" * 50)
    
    # Initialize components
    youtube_adapter = YouTubeAPIAdapter(api_key=settings.youtube_api_key)
    ollama_adapter = OllamaAdapter(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model
    )
    qa_service = YouTubeQAService(youtube_adapter, ollama_adapter)
    
    try:
        # Check if Ollama is ready
        print("🔍 Checking Ollama connection...")
        if not await ollama_adapter.health_check():
            print("❌ Ollama is not available. Please make sure it's running.")
            return
        print("✅ Ollama is ready!")
        
        playlist_url = str(settings.youtube_playlist_url)
        print(f"\n📋 Analyzing playlist: {playlist_url}")
        
        # Get playlist summary
        print("\n📝 Getting playlist summary...")
        summary_response = await qa_service.get_playlist_summary(playlist_url)
        print(f"📄 Summary: {summary_response.answer}")
        print(f"📚 Sources: {len(summary_response.sources)} videos analyzed")
        
        # Demo questions
        demo_questions = [
            "What kind of games do the SIDEMEN play in this playlist?",
            "How many videos are in this playlist?",
            "What can viewers expect from these videos?",
            "Are these videos recent or older content?",
        ]
        
        print("\n" + "=" * 50)
        print("🤖 Interactive Q&A Demo")
        print("=" * 50)
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n{i}. ❓ Question: {question}")
            print("   🤔 Thinking...")
            
            response = await qa_service.answer_question(question, playlist_url, max_videos=5)
            
            print(f"   ✅ Answer: {response.answer}")
            print(f"   📊 Confidence: {response.confidence:.1%}")
            
            if i < len(demo_questions):
                print("   " + "-" * 40)
        
        # Demo video search
        print("\n" + "=" * 50)
        print("🔍 Video Search Demo")
        print("=" * 50)
        
        search_queries = ["among us", "IQ", "sus"]
        
        for query in search_queries:
            print(f"\n🔎 Searching for: '{query}'")
            videos = await qa_service.search_videos(query, playlist_url, max_results=3)
            
            if videos:
                print(f"   Found {len(videos)} videos:")
                for j, video in enumerate(videos, 1):
                    print(f"   {j}. {video.title}")
            else:
                print("   No videos found")
        
        print("\n🎉 Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        await ollama_adapter.close()

if __name__ == "__main__":
    asyncio.run(demo_qa_system())