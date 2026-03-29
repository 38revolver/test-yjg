"""
기사 분석/통합/한국어 번역 - Claude API를 이용한 A4 한 장 리포트 생성
"""

import os
import logging

import anthropic

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")


def generate_report(articles: list[dict]) -> dict:
    """
    수집된 기사들을 분석/통합하여 한국어 A4 한 장 리포트를 생성합니다.

    Returns:
        {
            "title": "리포트 제목",
            "report_html": "HTML 형식의 리포트 본문",
            "sources": [{"source": "NYT", "title": "...", "url": "...", "image": "..."}],
            "generated_at": "..."
        }
    """
    if not articles:
        return {
            "title": "수집된 기사 없음",
            "report_html": "<p>현재 트럼프-이란 관련 최신 기사가 없습니다. 10분 후 다시 확인합니다.</p>",
            "sources": [],
            "images": [],
        }

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY가 설정되지 않았습니다")
        return {
            "title": "API 키 미설정",
            "report_html": "<p>ANTHROPIC_API_KEY 환경변수를 설정해주세요.</p>",
            "sources": [],
            "images": [],
        }

    # 기사 본문을 프롬프트로 구성
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"\n--- 기사 {i} [{article['source']}] ---\n"
        articles_text += f"제목: {article['title']}\n"
        articles_text += f"URL: {article['url']}\n"
        articles_text += f"본문:\n{article['full_text'][:3000]}\n"

    prompt = f"""다음은 뉴욕타임즈(NYT), BBC, CNBC에서 수집한 트럼프-이란 관련 최신 뉴스 기사들입니다.

{articles_text}

위 기사들을 분석하고 통합하여, 한국어로 A4 한 장 분량(약 1500~2000자)의 뉴스 브리핑 리포트를 작성해주세요.

작성 규칙:
1. HTML 형식으로 작성 (body 태그 없이 내용만)
2. 리포트 제목을 <h2> 태그로 시작
3. 핵심 요약을 먼저 3~4줄로 작성 (굵은 글씨)
4. 각 언론사의 보도 관점 차이를 분석
5. 주요 사실관계, 배경, 전망을 포함
6. 자연스러운 한국어로 번역/작성 (번역체 금지)
7. 각 단락은 <p> 태그 사용
8. 중요한 부분은 <strong> 태그 사용
9. 소제목이 필요하면 <h3> 태그 사용

첫 줄에 리포트 제목만 별도로 출력하고, 그 다음 줄부터 HTML 본문을 작성하세요.
형식:
TITLE: 리포트 제목
HTML:
(본문 HTML)"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text

        # 제목과 HTML 분리
        title = "트럼프-이란 뉴스 브리핑"
        report_html = response_text

        if "TITLE:" in response_text and "HTML:" in response_text:
            parts = response_text.split("HTML:", 1)
            title_part = parts[0]
            report_html = parts[1].strip()
            if "TITLE:" in title_part:
                title = title_part.split("TITLE:", 1)[1].strip()

        # 소스 및 이미지 정보
        sources = []
        images = []
        for article in articles:
            sources.append({
                "source": article["source"],
                "title": article["title"],
                "url": article["url"],
            })
            if article.get("image"):
                images.append({
                    "url": article["image"],
                    "source": article["source"],
                    "caption": article["title"],
                })

        logger.info("리포트 생성 완료: %s", title)
        return {
            "title": title,
            "report_html": report_html,
            "sources": sources,
            "images": images,
        }

    except Exception as e:
        logger.error("Claude API 호출 실패: %s", e)
        return {
            "title": "리포트 생성 실패",
            "report_html": f"<p>리포트 생성 중 오류가 발생했습니다: {e}</p>",
            "sources": [],
            "images": [],
        }
