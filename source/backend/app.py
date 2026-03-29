"""
Flask API 서버 - 스크래핑된 뉴스 기사 제공 + 10분 주기 스케줄링
"""

import json
import os
import logging

from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

from scraper import scrape_all

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
ARTICLES_FILE = os.path.join(DATA_DIR, "articles.json")


def _load_articles() -> dict:
    if not os.path.exists(ARTICLES_FILE):
        return {"last_updated": None, "total_count": 0, "articles": []}
    with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/api/articles", methods=["GET"])
def get_articles():
    """전체 기사 목록 반환"""
    data = _load_articles()
    return jsonify(data)


@app.route("/api/articles/<article_id>", methods=["GET"])
def get_article(article_id):
    """개별 기사 상세 반환"""
    data = _load_articles()
    for article in data.get("articles", []):
        if article["id"] == article_id:
            return jsonify(article)
    return jsonify({"error": "Article not found"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# 스케줄러: 10분마다 스크래핑
scheduler = BackgroundScheduler()
scheduler.add_job(scrape_all, "interval", minutes=10, id="scrape_job")
scheduler.start()

# 시작 시 즉시 한 번 스크래핑
logger.info("초기 스크래핑 실행")
scrape_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
