import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..base import Fetcher, RawPage
from registry import fetchers

@fetchers.register("http")
class HttpFetcher(Fetcher):
    def __init__(
        self,
        cache_dir: str = "data/raw/web_scrape/_cache",
        timeout: float = 10.0,
        user_agent: str = "westworld-research-bot/0.1",
        use_cache: bool = True,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}
        self.client = httpx.Client(headers=self.headers)
        self.use_cache = use_cache

    def _cache_path(self, url: str) -> Path:
        url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        return self.cache_dir / f"{url_hash}.json"

    def fetch(self, url: str) -> RawPage | None:
        cache_path = self._cache_path(url)

        if self.use_cache and cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            return RawPage(
                url=data["url"],
                content=data["content"],
                content_type=data["content_type"],
                fetched_at=datetime.fromisoformat(data["fetched_at"]),
                status_code=data["status_code"],
            )

        try:
            resp = self.client.get(url, timeout=self.timeout, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"[HttpFetcher] Failed to fetch {url}: {e}")
            return None

        content_type = "html" if "text/html" in resp.headers.get("content-type", "") else "text"

        page = RawPage(
            url=url,
            content=resp.text,
            content_type=content_type,
            fetched_at=datetime.now(timezone.utc),
            status_code=resp.status_code,
        )

        cache_path.write_text(
            json.dumps({
                "url": page.url,
                "content": page.content,
                "content_type": page.content_type,
                "fetched_at": page.fetched_at.isoformat(),
                "status_code": page.status_code,
            }, ensure_ascii=False),
            encoding="utf-8",
        )

        return page