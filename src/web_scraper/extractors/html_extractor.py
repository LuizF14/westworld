from datetime import datetime, timezone

import trafilatura

from ..base import Extractor, ExtractedDocument, RawPage
from registry import extractors

@extractors.register("html")
class HtmlExtractor(Extractor):
    def __init__(self, min_length: int = 200):
        self.min_length = min_length

    def extract(self, page: RawPage) -> ExtractedDocument | None:
        if page.content_type != "html":
            print(f"[HtmlExtractor] skip (content_type={page.content_type}): {page.url}")
            return None

        text = trafilatura.extract(
            page.content,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )

        if not text or len(text) < self.min_length:
            print(f"[HtmlExtractor] not enough text: {page.url}")
            return None

        metadata = trafilatura.extract_metadata(page.content)
        title = metadata.title if metadata else None

        return ExtractedDocument(
            url=page.url,
            title=title,
            text=text,
            extracted_at=datetime.now(timezone.utc),
        )