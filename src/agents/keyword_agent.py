import litellm
import hashlib

from dataclasses import dataclass, field

from .base import CharacterAgent
from registry import agents

CORE_KEYWORDS_SYSTEM_PROMPT = """You are a research assistant helping build character profiles for a role-playing LLM benchmark.
Given an introductory text about a character, generate a list of CORE KEYWORDS that capture the character's primary attributes: significant life events, personality traits, social relationships, and notable milestones.

Output format rule: respond with ONLY a numbered list, one keyword per line, in the format:
1. keyword
2. keyword
Do not include any preamble, introduction, headers, or closing remarks. The very first character of your response must be "1".

Rules:
- Each keyword must be a short phrase (a few words), not a full sentence.
- Keywords must be about the target character only, not about other characters mentioned in the text.
- Do not repeat similar keywords; each one should cover a distinct aspect of the character.
- Base keywords strictly on what is present or implied in the provided text.
"""

SUB_KEYWORDS_SYSTEM_PROMPT = """You are a research assistant helping build character profiles for a role-playing LLM benchmark.
Given a character, a core keyword about that character, and source text, generate specific and detailed SUB-KEYWORDS that expand on that core keyword.

Output format rule: respond with ONLY a numbered list, one sub-keyword per line, in the format:
1. sub-keyword
2. sub-keyword
Do not include any preamble, introduction, headers, or closing remarks. The very first character of your response must be "1".

Rules:
- Each sub-keyword must be a short phrase (a few words), not a full sentence.
- Sub-keywords must expand specifically on the given core keyword, not on the character in general.
- Do not repeat similar sub-keywords; each one should cover a distinct aspect.
- Base sub-keywords strictly on what is present or implied in the provided text.
"""

CONTEXT_SUMMARY_SYSTEM_PROMPT = """You are a research assistant preparing condensed reference material for a character profiling pipeline.
Summarize the given source text into a dense, information-rich summary about the target character.

Rules:
- Preserve concrete facts: names, dates, events, relationships, and specific details. Do not generalize them away.
- Remove redundant phrasing, filler, and repeated information across sources.
- Do not add commentary, headers, or meta-remarks about the summarization itself.
- Aim for a summary that is significantly shorter than the source but still detailed enough to answer specific questions about the character.
"""

@dataclass
class CoreKeyword:
    name: str
    sub_keywords: list[str] = field(default_factory=list)


@agents.register("keyword_agent")
class KeywordAgent(CharacterAgent):
    def __init__(
        self,
        model: str = "ollama/llama3",
        temperature: float = 0.3,
        num_core_keywords: int = 4,
        num_sub_keywords: int = 5,
        max_chars_per_source: int = 4000,
        max_total_chars: int = 20000,
        summary_trigger_chars: int = 6000,
    ):
        super().__init__(model, temperature)
        self.num_core_keywords = num_core_keywords
        self.num_sub_keywords = num_sub_keywords
        self.max_chars_per_source = max_chars_per_source
        self.max_total_chars = max_total_chars
        self.summary_trigger_chars = summary_trigger_chars
        self._context_summary_cache = {}

    def _summarize_context(self, raw_context: str) -> str:
        print(f"[context] summarizing {len(raw_context)} chars...")
        summary = self._complete(CONTEXT_SUMMARY_SYSTEM_PROMPT, raw_context)
        print(f"[context] summarized to {len(summary)} chars")
        return summary

    def _build_context(self, source_texts: list[str]) -> str:
        trimmed = [t[: self.max_chars_per_source] for t in source_texts]
        raw_context = "\n\n---\n\n".join(trimmed)[: self.max_total_chars]

        if len(raw_context) <= self.summary_trigger_chars:
            return raw_context

        cache_key = hashlib.sha256(raw_context.encode("utf-8")).hexdigest()
        if cache_key in self._context_summary_cache:
            return self._context_summary_cache[cache_key]

        summary = self._summarize_context(raw_context)
        self._context_summary_cache[cache_key] = summary
        return summary

    def _parse_list(self, raw_output: str) -> list[str]:
        items = []
        for line in raw_output.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            _, _, rest = line.partition(".")
            item = rest.strip() if rest else line
            if item:
                items.append(item)
        return items

    def generate_core_keywords(self, character_name: str, source_texts: list[str]) -> list[str]:
        if not source_texts:
            raise ValueError(f"No source text available for '{character_name}'.")

        context = self._build_context(source_texts)

        user_prompt = f"""Target character: {character_name}

Source text:
{context}

Generate {self.num_core_keywords} core keywords about {character_name} now."""

        response = self._complete(CORE_KEYWORDS_SYSTEM_PROMPT, user_prompt)
        return self._parse_list(response)

    def generate_sub_keywords(self, character_name: str, core_keyword: str, source_texts: list[str]) -> list[str]:
        if not source_texts:
            raise ValueError(f"No source text available for '{character_name}'.")

        context = self._build_context(source_texts)

        user_prompt = f"""Target character: {character_name}
Core keyword: {core_keyword}

Source text:
{context}

Generate {self.num_sub_keywords} sub-keywords about {character_name}'s "{core_keyword}" now."""

        response = self._complete(SUB_KEYWORDS_SYSTEM_PROMPT, user_prompt) 

        return self._parse_list(response)

    def generate_keywords(self, character_name: str, source_texts: list[str]) -> list[CoreKeyword]:
        core_names = self.generate_core_keywords(character_name, source_texts)

        core_keywords = []
        for name in core_names:
            sub_keywords = self.generate_sub_keywords(character_name, name, source_texts)
            core_keywords.append(CoreKeyword(name=name, sub_keywords=sub_keywords))

        return core_keywords