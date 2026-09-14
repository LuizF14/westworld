import hashlib

from .base import CharacterAgent
from registry import agents

CONTEXT_SUMMARY_SYSTEM_PROMPT = """You are a research assistant preparing condensed reference material for a character profiling pipeline.
Summarize the given source text into a dense, information-rich summary about the target character.

Rules:
- Write in connected prose (full sentences and paragraphs). Do NOT use bullet points, headers, or list formatting of any kind.
- Preserve concrete facts: names, dates, events, relationships, and specific details. Do not generalize them away.
- Preserve the relationships BETWEEN facts, not just the facts in isolation — explain how and why things happened, not just that they happened.
- Remove redundant phrasing, filler, and repeated information across sources.
- Do not add commentary, headers, or meta-remarks about the summarization itself.
- Aim for a summary that is significantly shorter than the source but still detailed enough to answer specific questions about the character.
"""

@agents.register("summary_agent")
class SummaryAgent(CharacterAgent):
    def __init__(
        self,
        model: str = "ollama/llama3",
        temperature: float = 0.3,
        input_max_size: int = 4000,
        summary_trigger_chars: int = 6000,
    ):
        super().__init__(model, temperature, input_max_size)
        self.summary_trigger_chars = summary_trigger_chars
        self._context_summary_cache = {}

    def summarize(self, texts: list[str]) -> str:
        raw_context = "\n\n---\n\n".join(texts)

        if len(raw_context) <= self.summary_trigger_chars:
            return raw_context

        cache_key = hashlib.sha256(raw_context.encode("utf-8")).hexdigest()
        if cache_key in self._context_summary_cache:
            return self._context_summary_cache[cache_key]
        
        print(f"[context] summarizing {len(raw_context)} chars...")
        summary = self._complete(CONTEXT_SUMMARY_SYSTEM_PROMPT, raw_context)        
        print(f"[context] summarized to {len(summary)} chars")

        self._context_summary_cache[cache_key] = summary
        return summary