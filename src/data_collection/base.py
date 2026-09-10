from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    source: str = ""  # name of the searcher, ex: "bing", "wikipedia"

class Searcher(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Run the search and returns the candidates."""
        ...