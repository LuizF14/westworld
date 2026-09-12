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
    ):
        self.model = model
        self.temperature = temperature

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
        )
        return response.choices[0].message.content