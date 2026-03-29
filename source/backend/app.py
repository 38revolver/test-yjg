"""
Flask API 서버 - 뉴스 수집 → 분석/통합 → 한국어 A4 리포트 제공
10분 주기 스케줄링
"""

import json
import os
import logging
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler

from scraper import scrape_all
from summarizer import generate_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
REPORT_FILE = os.path.join(DATA_DIR, "report.json")


def _load_report() -> dict:
    if not os.path.exists(REPORT_FILE):
        return {
            "title": "대기 중",
            "report_html": "<p>첫 번째 리포트를 생성하고 있습니다. 잠시만 기다려주세요...</p>",
            "sources": [],
            "images": [],
            "generated_at": None,
        }
    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline():
    """스크래핑 → 분석 → 리포트 저장 파이프라인"""
    logger.info("=== 파이프라인 시작 ===")

    # 1. 기사 수집 (각 언론사 3개씩)
    articles = scrape_all()
    if not articles:
        logger.warning("수집된 기사가 없습니다")

    # 2. Claude API로 분석/통합/번역
    report = generate_report(articles)
    report["generated_at"] = datetime.utcnow().isoformat()
    report["article_count"] = len(articles)

    # 3. 저장
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info("=== 파이프라인 완료: %d개 기사 → 리포트 생성 ===", len(articles))


@app.route("/api/report", methods=["GET"])
def get_report():
    """최신 통합 리포트 반환"""
    report = _load_report()
    return jsonify(report)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# 스케줄러: 10분마다 파이프라인 실행
scheduler = BackgroundScheduler()
scheduler.add_job(run_pipeline, "interval", minutes=10, id="pipeline_job")
scheduler.start()

# 시작 시 즉시 한 번 실행
logger.info("초기 파이프라인 실행")
run_pipeline()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
