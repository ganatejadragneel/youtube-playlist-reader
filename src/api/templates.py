from typing import List
from src.api.models import VideoResponse, QAResponse as APIQAResponse, PlaylistSummaryResponse, HealthResponse


def render_health_status(health: HealthResponse) -> str:
    """Render health status component."""
    youtube_status = "✅" if health.youtube_api else "❌"
    ollama_status = "✅" if health.ollama else "❌"
    
    youtube_color = "green" if health.youtube_api else "red"
    ollama_color = "green" if health.ollama else "red"
    
    return f"""
    <div class="inline-flex items-center space-x-4 text-sm">
        <span class="flex items-center">
            <span class="w-2 h-2 bg-{youtube_color}-500 rounded-full mr-1"></span>
            YouTube API: {youtube_status}
        </span>
        <span class="flex items-center">
            <span class="w-2 h-2 bg-{ollama_color}-500 rounded-full mr-1"></span>
            Ollama: {ollama_status}
        </span>
        <span class="text-gray-600">({health.message})</span>
    </div>
    """


def render_summary(summary: PlaylistSummaryResponse) -> str:
    """Render playlist summary component."""
    confidence_percent = int(summary.summary.confidence * 100)
    source_count = len(summary.summary.sources)
    
    return f"""
    <div class="bg-blue-50 p-4 rounded-lg">
        <h3 class="font-bold text-lg mb-2">{summary.title}</h3>
        <p class="text-gray-600 mb-2">Channel: {summary.channel_title} • {summary.video_count} videos</p>
        {f'<p class="text-sm text-gray-600 mb-3">Description: {summary.description}</p>' if summary.description else ''}
        <div class="bg-white p-4 rounded border">
            <h4 class="font-semibold mb-2">🤖 AI Analysis:</h4>
            <p class="text-gray-800 whitespace-pre-wrap">{summary.summary.answer}</p>
            <div class="mt-3 text-sm text-gray-600">
                <strong>Confidence:</strong> {confidence_percent}% • <strong>Sources:</strong> {source_count} videos analyzed
            </div>
        </div>
    </div>
    """


def render_qa_response(qa: APIQAResponse) -> str:
    """Render Q&A response component."""
    confidence_percent = int(qa.confidence * 100)
    processing_time = f"{qa.processing_time:.1f}" if qa.processing_time else "N/A"
    
    sources_html = ""
    if qa.sources:
        sources_items = "\n".join(f"<li>{source}</li>" for source in qa.sources)
        sources_html = f"""
        <details class="text-sm mt-3">
            <summary class="cursor-pointer text-blue-600 hover:text-blue-800 font-medium">View Sources ({len(qa.sources)} videos)</summary>
            <ul class="mt-2 list-disc list-inside text-gray-600 ml-4">
                {sources_items}
            </ul>
        </details>
        """
    
    return f"""
    <div class="bg-green-50 p-4 rounded-lg">
        <h4 class="font-semibold mb-2">🤖 Answer:</h4>
        <p class="text-gray-800 mb-3 whitespace-pre-wrap">{qa.answer}</p>
        <div class="text-sm text-gray-600">
            <strong>Confidence:</strong> {confidence_percent}% • <strong>Processing Time:</strong> {processing_time}s
        </div>
        {sources_html}
    </div>
    """


def render_video_card(video: VideoResponse) -> str:
    """Render a single video card."""
    # Truncate description if too long
    description = video.description
    if len(description) > 150:
        description = description[:150] + "..."
    
    # Format published date
    from datetime import datetime
    try:
        pub_date = datetime.fromisoformat(video.published_at.replace('Z', '+00:00'))
        formatted_date = pub_date.strftime('%Y-%m-%d')
    except:
        formatted_date = video.published_at[:10]  # Fallback
    
    return f"""
    <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        <h4 class="font-semibold text-blue-600 mb-1">
            <a href="https://youtube.com/watch?v={video.video_id}" target="_blank" class="hover:underline">
                {video.title}
            </a>
        </h4>
        <p class="text-sm text-gray-600 mb-2">📅 {formatted_date} • 📺 {video.channel_title}</p>
        {f'<p class="text-gray-700 text-sm">{description}</p>' if description.strip() else ''}
    </div>
    """


def render_video_list(videos: List[VideoResponse]) -> str:
    """Render a list of videos."""
    if not videos:
        return '<div class="text-gray-600 p-4 text-center">No videos found.</div>'
    
    video_cards = "\n".join(render_video_card(video) for video in videos)
    
    return f"""
    <div class="space-y-3">
        <div class="text-sm text-gray-600 mb-3">Found {len(videos)} video(s)</div>
        {video_cards}
    </div>
    """


def render_error(message: str) -> str:
    """Render error message."""
    return f"""
    <div class="text-red-600 p-4 bg-red-50 rounded-lg border border-red-200">
        <strong>Error:</strong> {message}
    </div>
    """