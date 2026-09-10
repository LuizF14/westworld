from dataclasses import dataclass, field
from data_collection.base import Searcher

@dataclass
class CharacterCollectionResult:
    character_name: str
    keywords: list[str] = field(default_factory=list)
    sub_keywords: dict[str, list[str]] = field(default_factory=dict)
    documents: list[dict] = field(default_factory=list)  # {url, keyword, clean_text}

class CharacterDataPipeline:
    def __init__(
        self,
        searcher: Searcher,
        # fetcher: Fetcher,
        # html_extractor: Extractor,
        # keyword_agent, 
        max_results_per_query: int = 5,
    ):
        self.searcher = searcher
        # self.fetcher = fetcher
        # self.html_extractor = html_extractor
        # self.keyword_agent = keyword_agent
        self.max_results_per_query = max_results_per_query

    def run(self, character_name: str, base_intro: str) -> CharacterCollectionResult:
        result = CharacterCollectionResult(character_name=character_name)

        return result

        # # 1. keywords centrais
        # result.keywords = self.keyword_agent.generate_core_keywords(base_intro)

        # # 2. sub-keywords + busca + fetch + extração
        # for kw in result.keywords:
        #     sub_kws = self.keyword_agent.generate_sub_keywords(character_name, kw)
        #     result.sub_keywords[kw] = sub_kws

        #     for sub_kw in sub_kws:
        #         search_results = self.searcher.search(sub_kw, self.max_results_per_query)
        #         for sr in search_results:
        #             raw_page = self.fetcher.fetch(sr.url)
        #             if raw_page is None:
        #                 continue
        #             clean_text = self.html_extractor.extract(raw_page)
        #             result.documents.append({
        #                 "url": sr.url,
        #                 "keyword": kw,
        #                 "sub_keyword": sub_kw,
        #                 "text": clean_text,
        #             })

        # return result