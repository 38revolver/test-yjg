import React, { useState, useEffect, useCallback } from "react";
import ArticleCard from "./components/ArticleCard";
import "./App.css";

const API_URL = "/api/articles";
const REFRESH_INTERVAL = 10 * 60 * 1000; // 10분

const SOURCE_LABELS = {
  NYT: "뉴욕타임즈",
  BBC: "BBC",
  CNBC: "CNBC",
};

function App() {
  const [articles, setArticles] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchArticles = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setArticles(data.articles || []);
      setLastUpdated(data.last_updated);
    } catch (err) {
      setError("기사를 불러오는데 실패했습니다: " + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchArticles();
    const interval = setInterval(fetchArticles, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchArticles]);

  const grouped = articles.reduce((acc, article) => {
    if (!acc[article.source]) acc[article.source] = [];
    acc[article.source].push(article);
    return acc;
  }, {});

  return (
    <div className="app">
      <header className="app-header">
        <h1>트럼프-이란 뉴스 모니터</h1>
        <div className="header-info">
          <span className="update-time">
            마지막 업데이트:{" "}
            {lastUpdated
              ? new Date(lastUpdated).toLocaleString("ko-KR")
              : "-"}
          </span>
          <span className="article-count">총 {articles.length}건</span>
          <button className="refresh-btn" onClick={fetchArticles} disabled={loading}>
            {loading ? "로딩 중..." : "새로고침"}
          </button>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <main className="a4-container">
        {loading && articles.length === 0 ? (
          <div className="loading">기사를 수집하고 있습니다...</div>
        ) : articles.length === 0 ? (
          <div className="empty">수집된 기사가 없습니다.</div>
        ) : (
          Object.entries(grouped).map(([source, items]) => (
            <section key={source} className="source-section">
              <h2 className="source-title">{SOURCE_LABELS[source] || source}</h2>
              {items.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </section>
          ))
        )}
      </main>

      <footer className="app-footer">
        <p>10분마다 자동 갱신 | 뉴욕타임즈, BBC, CNBC</p>
      </footer>
    </div>
  );
}

export default App;
