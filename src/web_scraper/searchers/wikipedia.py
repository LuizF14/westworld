import httpx
from ..base import Searcher, SearchResult
from registry import searchers

@searchers.register("wikipedia")
class WikipediaProvider(Searcher):
    API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, language: str = "en", user_agent: str = "westworld-research-bot/0.1",):
        self.api_url = f"https://{language}.wikipedia.org/w/api.php"
        self.headers = {"User-Agent": user_agent}
        self.client = httpx.Client(headers=self.headers)

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": max_results,
        }
        resp = self.client.get(self.api_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("query", {}).get("search", []):
            title = item["title"]
            url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
            results.append(SearchResult(
                title=title,
                url=url,
                snippet=item.get("snippet"),
                source="wikipedia",
            ))
        return results