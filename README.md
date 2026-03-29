# Trump-Iran 뉴스 모니터

NYT, BBC, CNBC에서 트럼프-이란 관련 뉴스를 10분마다 자동 수집하여 이미지와 함께 A4 한 장 분량으로 정리하는 웹 애플리케이션입니다.

## 기술 스택

- **Backend**: Python (Flask, BeautifulSoup4, APScheduler)
- **Frontend**: React 18
- **Proxy**: Nginx
- **Container**: Docker Compose

## 실행 방법

```bash
docker-compose up --build
```

브라우저에서 `http://localhost:32000` 접속

## 프로젝트 구조

```
source/
├── backend/     # Python 스크래퍼 + REST API
├── frontend/    # React 웹 앱
└── nginx/       # 리버스 프록시
data/            # 수집된 기사 데이터 (JSON)
```
