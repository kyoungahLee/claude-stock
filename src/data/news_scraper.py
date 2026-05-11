from dataclasses import dataclass, field
from datetime import datetime

import feedparser
import httpx
from bs4 import BeautifulSoup

from src.config import get_news_sources


@dataclass
class NewsArticle:
    title: str
    source: str
    url: str
    published: str
    summary: str = ""
    language: str = "en"


def fetch_rss_articles(source_name: str, rss_url: str, language: str = "en", max_articles: int = 10) -> list[NewsArticle]:
    articles = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:max_articles]:
            summary = ""
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary = soup.get_text()[:500]

            published = ""
            if hasattr(entry, "published"):
                published = entry.published
            elif hasattr(entry, "updated"):
                published = entry.updated

            articles.append(NewsArticle(
                title=entry.get("title", ""),
                source=source_name,
                url=entry.get("link", ""),
                published=published,
                summary=summary,
                language=language,
            ))
    except Exception:
        pass

    return articles


def fetch_all_news(max_per_source: int = 10) -> list[NewsArticle]:
    config = get_news_sources()
    all_articles = []

    for source in config.get("sources", {}).get("english", []):
        if not source.get("enabled", False):
            continue
        rss_url = source.get("rss", "")
        if rss_url:
            articles = fetch_rss_articles(
                source_name=source["name"],
                rss_url=rss_url,
                language="en",
                max_articles=max_per_source,
            )
            all_articles.extend(articles)

    for source in config.get("sources", {}).get("korean", []):
        if not source.get("enabled", False):
            continue
        rss_url = source.get("rss", "")
        if rss_url:
            articles = fetch_rss_articles(
                source_name=source["name"],
                rss_url=rss_url,
                language="ko",
                max_articles=max_per_source,
            )
            all_articles.extend(articles)

    return all_articles


def get_news_summary_text(articles: list[NewsArticle]) -> str:
    lines = []
    for i, article in enumerate(articles, 1):
        lines.append(f"[{i}] [{article.source}] {article.title}")
        if article.summary:
            lines.append(f"    {article.summary[:200]}")
        lines.append("")
    return "\n".join(lines)
