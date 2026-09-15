from dataclasses import dataclass, field

from tqdm import tqdm
import re

from .base import CharacterAgent
from registry import agents

def _build_category_system_prompt(category: str, description: str) -> str:
    return f"""You are a research assistant helping build character profiles for a role-playing LLM benchmark.
Given a source text about a character, generate a list of KEYWORDS about the target character that belong ONLY to the following category:

Category: {category.upper()}
Definition: {description}

Output format rule: respond with ONLY a numbered list, one keyword per line, in the format:
1. keyword
2. keyword
Do not include any preamble, introduction, headers, or closing remarks. The very first character of your response must be "1".
If no relevant keywords exist in this category for the given text, respond with exactly: NONE

Rules:
- Each keyword must be a short phrase (a few words), not a full sentence.
- Each keyword must clearly fit the category above. Discard anything that does not fit, even if interesting.
- Keywords must be about the target character only, except when the keyword IS about a related character (applicable only to the "characters" category).
- Do not repeat similar keywords; each one should cover a distinct aspect.
- Base keywords strictly on what is present or implied in the provided text.
"""

CATEGORY_DEFINITIONS = {
    "characters": "Other characters with a meaningful connection to the target (family, allies, rivals, love interests, mentors).",
    "places": "Locations significant to the character (origin, home, recurring settings).",
    "objects": "Items, artifacts, or tools closely associated with the character.",
    "events": "Specific incidents, milestones, or turning points involving the character.",
    "concepts": "Abilities, powers, ideologies, professions, or themes tied to the character.",
    "traits": "Personality traits, values, or behavioral patterns of the character.",
}

CATEGORY_SYSTEM_PROMPTS = {
    category: _build_category_system_prompt(category, description)
    for category, description in CATEGORY_DEFINITIONS.items()
}

@dataclass(frozen=True)
class CoreKeyword:
    name: str
    category: str

@agents.register("keyword_agent")
class KeywordAgent(CharacterAgent):
    def __init__(
        self,
        model: str = "ollama/llama3",
        temperature: float = 0.3,
        num_keywords_per_category: int = 4,
        input_max_size: int = 4000
    ):
        super().__init__(model, temperature, input_max_size)
        self.num_keywords_per_category = num_keywords_per_category
        
    def _parse_list(self, raw_output: str) -> list[str]:
        if raw_output.strip().upper() == "NONE":
            return []

        items = []
        for line in raw_output.strip().splitlines():
            line = line.strip()
            if not line:
                continue

            match = re.match(r"^\d+[\.\)]\s*(.+)$", line)
            if match:
                item = match.group(1).strip()
                if item:
                    items.append(item)

        return items

    def _extract_keywords_for_category(self, character_name: str, context: str, category: str) -> list[str]:
        system_prompt = CATEGORY_SYSTEM_PROMPTS[category]
        user_prompt = f"""Target character: {character_name}

Source text:
{context}

Generate up to {self.num_keywords_per_category} keywords in the "{category}" category about {character_name} now."""

        response = self._complete(system_prompt, user_prompt)
        return self._parse_list(response)

    def generate_keywords(self, character_name: str, context: str) -> list[CoreKeyword]:
        chunks = self._chunk_text(context, self.input_max_size)

        seen: set[tuple[str, str]] = set()
        keywords: list[CoreKeyword] = []

        total_calls = len(chunks) * len(CATEGORY_DEFINITIONS)
        with tqdm(total=total_calls, desc="Extracting keywords", unit="call") as pbar:
            for chunk in chunks:
                for category in CATEGORY_DEFINITIONS:
                    names = self._extract_keywords_for_category(character_name, chunk, category)
                    for name in names:
                        dedup_key = (category, name.strip().lower())
                        if dedup_key not in seen:
                            seen.add(dedup_key)
                            keywords.append(CoreKeyword(name=name, category=category))
                    pbar.update(1)

        return keywords