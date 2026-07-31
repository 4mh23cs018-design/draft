import time
from typing import AsyncGenerator, Dict, Any, Tuple
from openai import AsyncOpenAI
import tiktoken
from backend.core.config import settings
from backend.core.logging import logger

class OpenAIService:
    """LLM generation service supporting standard responses, streaming, and token metrics."""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.LLM_MODEL
        self._client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken encoder."""
        try:
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation
            return len(text.split())

    async def generate_answer(self, prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generate complete answer with latency and token usage metrics.
        """
        start_time = time.perf_counter()
        
        if not self._client:
            # Offline mock answer when no API key is provided
            mock_answer = (
                "Based on the provided context: "
                "The requested details were retrieved from the uploaded documents. "
                "If the specific detail is missing, I don't know."
            )
            elapsed = time.perf_counter() - start_time
            tokens = self.count_tokens(prompt) + self.count_tokens(mock_answer)
            return mock_answer, {
                "llm_latency_ms": round(elapsed * 1000, 2),
                "prompt_tokens": self.count_tokens(prompt),
                "completion_tokens": self.count_tokens(mock_answer),
                "total_tokens": tokens
            }

        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            elapsed = time.perf_counter() - start_time
            answer = response.choices[0].message.content or ""
            usage = response.usage

            metrics = {
                "llm_latency_ms": round(elapsed * 1000, 2),
                "prompt_tokens": usage.prompt_tokens if usage else self.count_tokens(prompt),
                "completion_tokens": usage.completion_tokens if usage else self.count_tokens(answer),
                "total_tokens": usage.total_tokens if usage else self.count_tokens(prompt + answer)
            }
            return answer, metrics

        except Exception as e:
            logger.error(f"OpenAI LLM API call error: {str(e)}")
            raise e

    async def stream_answer(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Stream answer tokens for real-time streaming response.
        """
        if not self._client:
            mock_tokens = [
                "Based ", "on ", "the ", "supplied ", "context, ",
                "here ", "is ", "the ", "retrieved ", "information."
            ]
            for token in mock_tokens:
                yield token
            return

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            stream=True
        )

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
