"""Research provider package — all real providers, no fake data."""

from assumption_zero.research.arxiv_provider import ArxivProvider
from assumption_zero.research.base import ResearchProvider
from assumption_zero.research.github_provider import GitHubProvider
from assumption_zero.research.hackernews_provider import HackerNewsProvider
from assumption_zero.research.news_provider import NewsSearchProvider
from assumption_zero.research.reddit_provider import RedditProvider
from assumption_zero.research.searxng_provider import SearXNGProvider
from assumption_zero.research.web_search_provider import WebSearchProvider
from assumption_zero.research.wikipedia_provider import WikipediaProvider

__all__ = [
    "ArxivProvider",
    "GitHubProvider",
    "HackerNewsProvider",
    "NewsSearchProvider",
    "RedditProvider",
    "ResearchProvider",
    "SearXNGProvider",
    "WebSearchProvider",
    "WikipediaProvider",
]
