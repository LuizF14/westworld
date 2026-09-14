from dataclasses import dataclass, field
from web_scraper.base import Searcher, Fetcher, Extractor
from agents.keyword_agent import KeywordAgent

@dataclass 
class CharacterExtendedInfo:
    character_name: str
    keywords: list[str] = field(default_factory=list)
    main_documents: list[str] = field(default_factory=list)
    extended_documents: list[str] = field(default_factory=list)


class CharacterExtendedInfoPipeline:
    def __init__(
        self,
        base_searcher: Searcher,
        keyword_searcher: Searcher,
        fetcher: Fetcher,
        html_extractor: Extractor,
        keyword_agent: KeywordAgent,
        max_results_per_query: int = 5,
    ):
        self.base_searcher = base_searcher
        self.keyword_searcher = keyword_searcher
        self.fetcher = fetcher
        self.html_extractor = html_extractor
        self.max_results_per_query = max_results_per_query
        self.keyword_agent = keyword_agent

    def run(self, character_name: str):
        base_search_results = self.base_searcher.search(character_name, self.max_results_per_query)

        print(f"\n{len(base_search_results)} results for '{character_name}':\n")
        for r in base_search_results:
            print(f"- {r.title}\n  {r.url}")

        main_documents = []
        for r in base_search_results:
            page = self.fetcher.fetch(r.url)
            if page is None:
                print(f"[skip:fetch] {r.url}")
                continue
    
            doc = self.html_extractor.extract(page)
            if doc is None:
                print(f"[skip:extract] {r.url}")
                continue
    
            print(f"[ok] {r.url} -> {len(doc.text)} chars")
            main_documents.append(doc.text)

        if not main_documents:
            raise RuntimeError(f"No document extracted to '{character_name}'.")

        keywords = self.keyword_agent.generate_keywords(character_name, main_documents)

        return CharacterExtendedInfo(
            character_name=character_name,
            keywords=keywords,
            main_documents=main_documents,
            extended_documents=[]
        )

        