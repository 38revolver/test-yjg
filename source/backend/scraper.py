"""
뉴스 스크래퍼 - NYT, BBC, CNBC에서 Trump-Iran 관련 기사 수집 및 본문 추출
"""

import json
import os
import hashlib
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import trafilatura

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
ARTICLES_PER_SOURCE = 3


def _article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _extract_full_text(url: str) -> str | None:
    """URL에서 기사 본문 전체를 추출"""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            return text
    except Exception as e:
        logger.warning("본문 추출 실패 (%s): %s", url, e)
    return None


def _extract_image_from_page(url: str) -> str | None:
    """기사 페이지에서 대표 이미지(og:image) 추출"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            return og["content"]
    except Exception:
        pass
    return None


def scrape_bbc() -> list[dict]:
    """BBC News RSS에서 Trump/Iran 관련 기사 수집 + 본문 추출"""
    articles = []
    try:
        rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "xml")

        for item in soup.find_all("item")[:40]:
            title = item.title.text if item.title else ""
            desc = item.description.text if item.description else ""
            combined = (title + " " + desc).lower()

            if not any(kw in combined for kw in ["trump", "iran"]):
                continue

            link = item.link.text if item.link else ""
            if not link:
                continue

            full_text = _extract_full_text(link)
            if not full_text:
                continue

            thumb = item.find("media:thumbnail")
            image = thumb["url"] if thumb and thumb.get("url") else _extract_image_from_page(link)

            articles.append({
                "id": _article_id(link),
                "title": title,
                "full_text": full_text,
                "url": link,
                "image": image,
                "source": "BBC",
                "scraped_at": datetime.utcnow().isoformat(),
            })

            if len(articles) >= ARTICLES_PER_SOURCE:
                break

    except Exception as e:
        logger.error("BBC 스크래핑 실패: %s", e)
    return articles


def scrape_nyt() -> list[dict]:
    """NYT RSS에서 Trump/Iran 관련 기사 수집 + 본문 추출"""
    articles = []
    try:
        rss_url = "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")

        for item in soup.find_all("item")[:40]:
            title = item.title.text if item.title else ""
            desc = item.description.text if item.description else ""
            combined = (title + " " + desc).lower()

            if not any(kw in combined for kw in ["trump", "iran"]):
                continue

            link = item.link.text if item.link else ""
            if not link:
                continue

            full_text = _extract_full_text(link)
            if not full_text:
                continue

            media = item.find("media:content")
            image = media["url"] if media and media.get("url") else _extract_image_from_page(link)

            articles.append({
                "id": _article_id(link),
                "title": title,
                "full_text": full_text,
                "url": link,
                "image": image,
                "source": "NYT",
                "scraped_at": datetime.utcnow().isoformat(),
            })

            if len(articles) >= ARTICLES_PER_SOURCE:
                break

    except Exception as e:
        logger.error("NYT 스크래핑 실패: %s", e)
    return articles


def scrape_cnbc() -> list[dict]:
    """CNBC RSS에서 Trump/Iran 관련 기사 수집 + 본문 추출"""
    articles = []
    try:
        rss_url = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")

        for item in soup.find_all("item")[:40]:
            title = item.title.text if item.title else ""
            desc = item.description.text if item.description else ""
            combined = (title + " " + desc).lower()

            if not any(kw in combined for kw in ["trump", "iran"]):
                continue

            link = item.link.text if item.link else ""
            if not link:
                continue

            full_text = _extract_full_text(link)
            if not full_text:
                continue

            media = item.find("media:content") or item.find("media:thumbnail")
            image = media["url"] if media and media.get("url") else _extract_image_from_page(link)

            articles.append({
                "id": _article_id(link),
                "title": title,
                "full_text": full_text,
                "url": link,
                "image": image,
                "source": "CNBC",
                "scraped_at": datetime.utcnow().isoformat(),
            })

            if len(articles) >= ARTICLES_PER_SOURCE:
                break

    except Exception as e:
        logger.error("CNBC 스크래핑 실패: %s", e)
    return articles


def scrape_all() -> list[dict]:
    """모든 소스에서 기사 수집 (각 3개씩, 본문 포함)"""
    logger.info("스크래핑 시작...")
    all_articles = []

    all_articles.extend(scrape_nyt())
    logger.info("NYT: %d개 수집", len([a for a in all_articles if a["source"] == "NYT"]))

    all_articles.extend(scrape_bbc())
    logger.info("BBC: %d개 수집", len([a for a in all_articles if a["source"] == "BBC"]))

    all_articles.extend(scrape_cnbc())
    logger.info("CNBC: %d개 수집", len([a for a in all_articles if a["source"] == "CNBC"]))

    # 중복 제거
    seen = set()
    unique = []
    for article in all_articles:
        if article["id"] not in seen:
            seen.add(article["id"])
            unique.append(article)

    logger.info("스크래핑 완료: 총 %d개 기사 수집 (본문 포함)", len(unique))
    return unique


if __name__ == "__main__":
    articles = scrape_all()
    for a in articles:
        print(f"[{a['source']}] {a['title']} ({len(a['full_text'])} chars)")
