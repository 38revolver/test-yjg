import React, { useState, useEffect, useCallback } from "react";
import "./App.css";

const API_URL = "/api/report";
const REFRESH_INTERVAL = 10 * 60 * 1000; // 10분

const SOURCE_LABELS = {
  NYT: "뉴욕타임즈",
  BBC: "BBC",
  CNBC: "CNBC",
};

function App() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReport = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setReport(data);
    } catch (err) {
      setError("리포트를 불러오는데 실패했습니다: " + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReport();
    const interval = setInterval(fetchReport, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchReport]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>트럼프-이란 뉴스 브리핑</h1>
        <div className="header-info">
          <span className="update-time">
            마지막 업데이트:{" "}
            {report?.generated_at
              ? new Date(report.generated_at).toLocaleString("ko-KR")
              : "-"}
          </span>
          {report?.article_count != null && (
            <span className="article-count">분석 기사: {report.article_count}건</span>
          )}
          <button className="refresh-btn" onClick={fetchReport} disabled={loading}>
            {loading ? "로딩 중..." : "새로고침"}
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="a4-container">
        {loading && !report ? (
          <div className="loading">기사를 수집하고 분석하고 있습니다...</div>
        ) : report ? (
          <>
            {/* 이미지 갤러리 */}
            {report.images && report.images.length > 0 && (
              <div className="image-gallery">
                {report.images.map((img, idx) => (
                  <figure key={idx} className="gallery-item">
                    <img
                      src={img.url}
                      alt={img.caption}
                      onError={(e) => { e.target.parentElement.style.display = "none"; }}
                    />
                    <figcaption>
                      <span className="img-source">{SOURCE_LABELS[img.source] || img.source}</span>
                      {" "}{img.caption}
                    </figcaption>
                  </figure>
                ))}
              </div>
            )}

            {/* 리포트 본문 */}
            <div
              className="report-content"
              dangerouslySetInnerHTML={{ __html: report.report_html }}
            />

            {/* 출처 */}
            {report.sources && report.sources.length > 0 && (
              <div className="sources-section">
                <h3>참고 기사</h3>
                <ul>
                  {report.sources.map((src, idx) => (
                    <li key={idx}>
                      <span className="src-badge">{SOURCE_LABELS[src.source] || src.source}</span>
                      <a href={src.url} target="_blank" rel="noopener noreferrer">
                        {src.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <div className="empty">리포트가 없습니다.</div>
        )}
      </main>

      <footer className="app-footer">
        <p>10분마다 자동 갱신 | 뉴욕타임즈, BBC, CNBC 기사 분석 및 통합</p>
      </footer>
    </div>
  );
}

export default App;
