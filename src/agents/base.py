from abc import ABC, abstractmethod

class CharacterAgent(ABC):
    @abstractmethod
    def generate_description(self, character_name: str, source_texts: list[str]) -> str:
        """Synthesizes a unique and cohesive description of the character from raw texts."""
        ...