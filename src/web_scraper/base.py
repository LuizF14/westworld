from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str | None = None
    source: str = ""  # name of the searcher, ex: "bing", "wikipedia"

@dataclass
class RawPage:
    url: str
    content: str            # HTML bruto ou texto, dependendo do fetcher
    content_type: str       # "html", "pdf", "text", etc.
    fetched_at: datetime
    status_code: int | None = None

class Searcher(ABC):
    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Run the search and returns the candidates."""
        ...

class Fetcher(ABC):
    @abstractmethod
    def fetch(self, url: str) -> RawPage | None:
        """Downloads the content of an URL. Returns None if fails."""
        ...