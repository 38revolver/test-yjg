"""
뉴스 스크래퍼 - NYT, BBC, CNBC에서 Trump-Iran 관련 기사 수집
"""

import json
import os
import hashlib
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
SEARCH_KEYWORDS = ["trump iran", "trump iran war", "trump iran nuclear"]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def scrape_bbc() -> list[dict]:
    """BBC News에서 Trump Iran 관련 기사 스크래핑"""
    articles = []
    try:
        url = "https://www.bbc.co.uk/search?q=trump+iran+war&edgeauth=eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for item in soup.select('[data-testid="default-promo"]')[:5]:
            title_el = item.select_one("h2, .ssrcss-6arcww-PromoHeadline")
            summary_el = item.select_one("p, .ssrcss-1q0x1qg-Paragraph")
            link_el = item.select_one("a[href]")
            img_el = item.select_one("img[src]")

            if not title_el or not link_el:
                continue

            article_url = link_el["href"]
            if not article_url.startswith("http"):
                article_url = "https://www.bbc.co.uk" + article_url

            articles.append({
                "id": _article_id(article_url),
                "title": title_el.get_text(strip=True),
                "summary": summary_el.get_text(strip=True) if summary_el else "",
                "url": article_url,
                "image": img_el["src"] if img_el else None,
                "source": "BBC",
                "scraped_at": datetime.utcnow().isoformat(),
            })
    except Exception as e:
        logger.error("BBC 스크래핑 실패: %s", e)

    # RSS 폴백
    if not articles:
        try:
            rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
            resp = requests.get(rss_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "xml")
            for item in soup.find_all("item")[:20]:
                title = item.title.text if item.title else ""
                desc = item.description.text if item.description else ""
                if any(kw in (title + " " + desc).lower() for kw in ["trump", "iran"]):
                    link = item.link.text if item.link else ""
                    thumb = item.find("media:thumbnail")
                    articles.append({
                        "id": _article_id(link),
                        "title": title,
                        "summary": desc,
                        "url": link,
                        "image": thumb["url"] if thumb and thumb.get("url") else None,
                        "source": "BBC",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
        except Exception as e:
            logger.error("BBC RSS 스크래핑 실패: %s", e)

    return articles


def scrape_nyt() -> list[dict]:
    """New York Times에서 Trump Iran 관련 기사 스크래핑 (RSS)"""
    articles = []
    try:
        rss_url = "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")

        for item in soup.find_all("item")[:30]:
            title = item.title.text if item.title else ""
            desc = item.description.text if item.description else ""
            combined = (title + " " + desc).lower()

            if any(kw in combined for kw in ["trump", "iran"]):
                link = item.link.text if item.link else ""
                media = item.find("media:content")
                articles.append({
                    "id": _article_id(link),
                    "title": title,
                    "summary": desc,
                    "url": link,
                    "image": media["url"] if media and media.get("url") else None,
                    "source": "NYT",
                    "scraped_at": datetime.utcnow().isoformat(),
                })
    except Exception as e:
        logger.error("NYT 스크래핑 실패: %s", e)
    return articles


def scrape_cnbc() -> list[dict]:
    """CNBC에서 Trump Iran 관련 기사 스크래핑 (RSS)"""
    articles = []
    try:
        rss_url = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"
        resp = requests.get(rss_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "xml")

        for item in soup.find_all("item")[:30]:
            title = item.title.text if item.title else ""
            desc = item.description.text if item.description else ""
            combined = (title + " " + desc).lower()

            if any(kw in combined for kw in ["trump", "iran"]):
                link = item.link.text if item.link else ""
                media = item.find("media:content") or item.find("media:thumbnail")
                articles.append({
                    "id": _article_id(link),
                    "title": title,
                    "summary": BeautifulSoup(desc, "html.parser").get_text(strip=True),
                    "url": link,
                    "image": media["url"] if media and media.get("url") else None,
                    "source": "CNBC",
                    "scraped_at": datetime.utcnow().isoformat(),
                })
    except Exception as e:
        logger.error("CNBC 스크래핑 실패: %s", e)
    return articles


def scrape_all() -> list[dict]:
    """모든 소스에서 기사를 수집하고 data/ 디렉토리에 저장"""
    logger.info("스크래핑 시작...")
    all_articles = []

    all_articles.extend(scrape_nyt())
    all_articles.extend(scrape_bbc())
    all_articles.extend(scrape_cnbc())

    # 중복 제거
    seen = set()
    unique = []
    for article in all_articles:
        if article["id"] not in seen:
            seen.add(article["id"])
            unique.append(article)

    # 저장
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, "articles.json")
    data = {
        "last_updated": datetime.utcnow().isoformat(),
        "total_count": len(unique),
        "articles": unique,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("스크래핑 완료: %d개 기사 수집", len(unique))
    return unique


if __name__ == "__main__":
    scrape_all()
