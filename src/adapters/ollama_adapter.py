import asyncio
from typing import List, Optional

import httpx
from loguru import logger

from src.interfaces.llm_repository import LLMRepository


class OllamaAdapter(LLMRepository):
    """Concrete implementation of LLM repository using Ollama."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from Ollama given a prompt and optional context."""
        try:
            # Build the full prompt with context if provided
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}\n\nAnswer:"

            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {}
            }
            
            if max_tokens:
                payload["options"]["num_predict"] = max_tokens

            logger.info(f"Sending request to Ollama: {self.model}")
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            generated_text = result.get("response", "").strip()
            logger.info(f"Ollama response generated: {len(generated_text)} characters")
            
            return generated_text

        except httpx.TimeoutException:
            logger.error(f"Timeout when calling Ollama at {self.base_url}")
            raise Exception("Ollama request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e.response.status_code}")
            raise Exception(f"Ollama HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise Exception(f"Ollama error: {str(e)}")

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for the given text using Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": text
            }

            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            embedding = result.get("embedding", [])
            if not embedding:
                raise Exception("No embedding returned from Ollama")
            
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning("Embeddings endpoint not available, using sentence-transformers fallback")
                # Fallback to local embedding generation
                return await self._generate_local_embedding(text)
            logger.error(f"HTTP error from Ollama embeddings: {e.response.status_code}")
            raise Exception(f"Ollama embeddings error: {e.response.status_code}")
        except Exception as e:
            logger.warning(f"Ollama embeddings failed, using fallback: {e}")
            return await self._generate_local_embedding(text)

    async def _generate_local_embedding(self, text: str) -> List[float]:
        """Fallback method using sentence-transformers for embeddings."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Load model (this will be cached after first use)
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embedding
            embedding = model.encode(text, convert_to_tensor=False)
            
            # Convert to list of floats
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate local embedding: {e}")
            raise Exception(f"Embedding generation failed: {str(e)}")

    async def health_check(self) -> bool:
        """Check if Ollama is available and the model is loaded."""
        try:
            # Check if Ollama is running
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            # Check if our model is available
            tags_data = response.json()
            models = [model["name"] for model in tags_data.get("models", [])]
            
            model_available = any(self.model in model for model in models)
            
            if not model_available:
                logger.warning(f"Model {self.model} not found. Available models: {models}")
                return False
            
            # Test a simple generation
            test_response = await self.generate_response(
                "Hello", 
                max_tokens=10
            )
            
            success = len(test_response) > 0
            logger.info(f"Ollama health check: {'✅ PASS' if success else '❌ FAIL'}")
            return success
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()