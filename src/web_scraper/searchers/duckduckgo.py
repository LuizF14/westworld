from ddgs import DDGS
from ddgs.exceptions import RatelimitException, TimeoutException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..base import Searcher, SearchResult
from registry import searchers

@searchers.register("duckduckgo")
class DuckDuckGoProvider(Searcher):
    def __init__(
        self,
        region: str = "wt-wt",
        safesearch: str = "moderate",
        backend: str = "auto",
        timeout: int = 10,
    ):
        self.region = region
        self.safesearch = safesearch
        self.backend = backend
        self.timeout = timeout

    @retry(
        retry=retry_if_exception_type((RatelimitException, TimeoutException)),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _text_search(self, query: str, max_results: int) -> list[dict]:
        with DDGS(timeout=self.timeout) as ddgs:
            return ddgs.text(
                query,
                region=self.region,
                safesearch=self.safesearch,
                backend=self.backend,
                max_results=max_results,
            )

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        try:
            raw_results = self._text_search(query, max_results)
        except (RatelimitException, TimeoutException):
            print("DuckDuckGo search failed after retries for query=%r", query)
            return []

        results = []
        for item in raw_results:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body"),
                    source="duckduckgo",
                )
            )
        return results