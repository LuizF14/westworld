from dataclasses import dataclass, field

from tqdm import tqdm

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

@agents.register("keyword_agent")
class KeywordAgent(CharacterAgent):
    def __init__(
        self,
        model: str = "ollama/llama3",
        temperature: float = 0.3,
        num_core_keywords: int = 4,
        num_sub_keywords: int = 5,
        input_max_size: int = 4000
    ):
        super().__init__(model, temperature, input_max_size)
        self.num_core_keywords = num_core_keywords
        self.num_sub_keywords = num_sub_keywords
        
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

    def _extract_keywords(self, character_name: str, context: str) -> list[str]:
        user_prompt = f"""Target character: {character_name}

Source text:
{context}

Generate {self.num_core_keywords} core keywords about {character_name} now."""

        response = self._complete(CORE_KEYWORDS_SYSTEM_PROMPT, user_prompt)
        return self._parse_list(response)

    def generate_keywords(self, character_name: str, context: str) -> list[str]:
        chunks = self._chunk_text(context, self.input_max_size)

        core_keywords = set()
        for chunk in tqdm(chunks, desc="Extracting keywords", unit="chunk"):
            names = self._extract_keywords(character_name, chunk)
            core_keywords.update(names)

        return list(core_keywords)