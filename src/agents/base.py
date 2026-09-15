import re
import time
from abc import ABC, abstractmethod

import litellm
from litellm.exceptions import RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt


def _wait_for_rate_limit(retry_state):
    exception = retry_state.outcome.exception()
    match = re.search(r"try again in ([\d.]+)s", str(exception))
    if match:
        wait_time = float(match.group(1)) + 0.5  # margem de segurança
    else:
        wait_time = min(2 * (2 ** retry_state.attempt_number), 60)

    print(f"[rate limit] tentativa {retry_state.attempt_number} falhou, aguardando {wait_time:.1f}s...")
    return wait_time


class CharacterAgent(ABC):
    def __init__(
        self,
        model: str = "ollama/llama3",
        temperature: float = 0.3,
        input_max_size: int = 4000,
        fallback_models: list[str] | None = None,
    ):
        self.model = model
        self.temperature = temperature
        self.input_max_size = input_max_size
        self.fallback_models = fallback_models or []

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=_wait_for_rate_limit,
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        response = litellm.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.temperature,
            fallbacks=self.fallback_models,
        )
        return response.choices[0].message.content

    def _chunk_text(self, text: str | list[str], max_chars: int, overlap: int = 200) -> list[str]:
        if isinstance(text, list):
            chunks = []
            for item in text:
                chunks += self._chunk_single_text(item, max_chars, overlap)
            return chunks

        return self._chunk_single_text(text, max_chars, overlap)

    def _chunk_single_text(self, text: str, max_chars: int, overlap: int = 200) -> list[str]:
        if len(text) <= max_chars:
            return [text.strip()] if text.strip() else []

        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunk = text[start:end]

            if end < len(text):
                last_break = max(chunk.rfind("\n\n"), chunk.rfind(". "))
                if last_break > max_chars * 0.5:
                    chunk = chunk[: last_break + 1]
                    end = start + last_break + 1

            chunks.append(chunk.strip())
            start = end - overlap if end < len(text) else end

        return [c for c in chunks if c]