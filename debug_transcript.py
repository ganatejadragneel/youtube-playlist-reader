import asyncio
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

async def debug_transcript():
    print("🔍 Debugging transcript extraction...")
    
    # Test videos that are more likely to have transcripts
    test_videos = [
        "BaW_jenozKc",  # YouTube official video
        "LXb3EKWsInQ",  # MKBHD tech video
        "tgbNymZ7vqY",  # Crash Course video (educational)
    ]
    
    for video_id in test_videos:
        print(f"\n📺 Testing video: {video_id}")
        
        try:
            # List available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print(f"✅ Available transcripts for {video_id}:")
            
            for transcript in transcript_list:
                print(f"  - Language: {transcript.language}")
                print(f"  - Language Code: {transcript.language_code}")
                print(f"  - Generated: {transcript.is_generated}")
                print(f"  - Translatable: {transcript.is_translatable}")
            
            # Try to get any available transcript
            try:
                # First try manual transcripts
                transcript = transcript_list.find_manually_created_transcript(['en'])
                print("  📝 Found manual English transcript")
            except:
                try:
                    # Then try auto-generated English
                    transcript = transcript_list.find_generated_transcript(['en'])
                    print("  🤖 Found auto-generated English transcript")
                except:
                    # Try any available language
                    available_transcripts = list(transcript_list)
                    if available_transcripts:
                        transcript = available_transcripts[0]
                        print(f"  🌐 Using transcript in {transcript.language}")
                    else:
                        print("  ❌ No transcripts available")
                        continue
            
            # Fetch and format the transcript
            transcript_data = transcript.fetch()
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
            
            print(f"  ✅ Transcript length: {len(formatted_transcript)} characters")
            print(f"  📄 Preview: {formatted_transcript[:200]}...")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_transcript())