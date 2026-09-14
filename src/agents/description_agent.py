import litellm

from .base import CharacterAgent
from registry import agents

SYSTEM_PROMPT = """You are a research assistant helping build character profiles for a role-playing LLM benchmark.
Given raw text snippets collected from the web, write ONE coherent, well-organized description of a SINGLE target character.

Critical rule: the source texts may contain information about OTHER characters (family members, allies, villains, cast members from the same franchise). You MUST IGNORE all content that is not directly about the target character. Do not describe, summarize, or mention other characters except briefly when describing the target character's relationships to them.

Output format rule: respond with ONLY the description text itself. Do not include any preamble, introduction, headers, labels, or closing remarks such as "Here is the description of X:" or "I hope this helps." The very first word of your response must be the first word of the description.

Rules:
- Base the description strictly on the provided source texts. Do not invent facts.
- Cover, when available: background/origin, personality traits, key relationships, notable events, and speech/behavior patterns — all from the perspective of the target character only.
- Write in clear, neutral prose (not bullet points, not section headers).
- If sources conflict about the target character, mention the discrepancy briefly rather than picking one silently.
- Keep it focused and avoid repeating the same fact multiple times, even if it appears in multiple sources.
"""


@agents.register("description_agent")
class DescriptionAgent(CharacterAgent):
    def __init__(
        self,
        model: str = "ollama/llama3",
        temperature: float = 0.3,
        input_max_size: int = 4000
    ):
        super().__init__(model, temperature, input_max_size)

    def _build_context(self, source_texts: list[str]) -> str:
        trimmed = [t[: self.input_max_size] for t in source_texts]
        context = "\n\n---\n\n".join(trimmed)
        return context

    def generate_description(self, character_name: str, source_texts: list[str]) -> str:
        if not source_texts:
            raise ValueError(f"No source text available for '{character_name}'.")

        context = self._build_context(source_texts)

        user_prompt = f"""Target character: {character_name}

IMPORTANT: Write about {character_name} ONLY. If the source texts mention other characters, ignore them unless directly relevant to describing {character_name}'s relationships.

Source texts:
{context}

Write the unified character description of {character_name} now."""

        return self._complete(SYSTEM_PROMPT, user_prompt).strip()