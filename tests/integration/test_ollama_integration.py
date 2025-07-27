import pytest
from src.adapters.ollama_adapter import OllamaAdapter
from src.config import settings


class TestOllamaIntegration:
    """Integration tests for Ollama adapter against real Ollama instance."""

    @pytest.fixture
    async def ollama_adapter(self):
        """Create Ollama adapter with real configuration."""
        adapter = OllamaAdapter(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model
        )
        yield adapter
        await adapter.close()

    @pytest.mark.asyncio
    async def test_ollama_health_check(self, ollama_adapter):
        """Test that Ollama is running and the model is available."""
        is_healthy = await ollama_adapter.health_check()
        
        if not is_healthy:
            pytest.skip("Ollama is not running or model is not available")
        
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_ollama_simple_generation(self, ollama_adapter):
        """Test basic text generation with Ollama."""
        # First check if Ollama is available
        if not await ollama_adapter.health_check():
            pytest.skip("Ollama is not running or model is not available")
        
        response = await ollama_adapter.generate_response(
            "What is 2 + 2?",
            max_tokens=50
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"Ollama response: {response}")

    @pytest.mark.asyncio
    async def test_ollama_with_context(self, ollama_adapter):
        """Test text generation with context."""
        # First check if Ollama is available
        if not await ollama_adapter.health_check():
            pytest.skip("Ollama is not running or model is not available")
        
        context = "This is a playlist about SIDEMEN playing Among Us games."
        question = "What type of content is this?"
        
        response = await ollama_adapter.generate_response(
            question,
            context=context,
            max_tokens=100
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"Ollama response with context: {response}")

    @pytest.mark.asyncio
    async def test_ollama_youtube_analysis(self, ollama_adapter):
        """Test Ollama analyzing YouTube video content."""
        # First check if Ollama is available
        if not await ollama_adapter.health_check():
            pytest.skip("Ollama is not running or model is not available")
        
        # Simulate analyzing a SIDEMEN video
        video_context = """
        Video Title: SIDEMEN play AMONG US but everyone has -200 IQ
        Channel: MoreSidemen
        Description: The Sidemen play Among Us with hilarious moments and terrible gameplay decisions.
        """
        
        question = "What kind of content is this and what should viewers expect?"
        
        response = await ollama_adapter.generate_response(
            question,
            context=video_context,
            max_tokens=150
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        print(f"YouTube analysis response: {response}")
        
        # Check that response mentions relevant keywords
        response_lower = response.lower()
        # At least one of these should be mentioned
        relevant_keywords = ["among us", "game", "sidemen", "funny", "entertainment"]
        assert any(keyword in response_lower for keyword in relevant_keywords)