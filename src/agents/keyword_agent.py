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

    def generate_core_keywords(self, character_name: str, context: str) -> list[str]:
        user_prompt = f"""Target character: {character_name}

Source text:
{context}

Generate {self.num_core_keywords} core keywords about {character_name} now."""

        response = self._complete(CORE_KEYWORDS_SYSTEM_PROMPT, user_prompt)
        return self._parse_list(response)

    def generate_sub_keywords(self, character_name: str, core_keyword: str, context: str) -> list[str]:
        user_prompt = f"""Target character: {character_name}
Core keyword: {core_keyword}

Source text:
{context}

Generate {self.num_sub_keywords} sub-keywords about {character_name}'s "{core_keyword}" now."""

        response = self._complete(SUB_KEYWORDS_SYSTEM_PROMPT, user_prompt) 

        return self._parse_list(response)

    def generate_keywords(self, character_name: str, context: str) -> list[CoreKeyword]:
        chunks = self._chunk_text(context, self.input_max_size)

        core_name_chunk_pairs: list[tuple[str, str]] = []
        for chunk in tqdm(chunks, desc="Extraindo core keywords", unit="chunk"):
            names = self.generate_core_keywords(character_name, chunk)
            core_name_chunk_pairs += [(name, chunk) for name in names]

        core_keywords = []
        for name, source_chunk in tqdm(core_name_chunk_pairs, desc="Gerando sub-keywords", unit="keyword"):
            sub_keywords = self.generate_sub_keywords(character_name, name, source_chunk)
            core_keywords.append(CoreKeyword(name=name, sub_keywords=sub_keywords))

        return core_keywords