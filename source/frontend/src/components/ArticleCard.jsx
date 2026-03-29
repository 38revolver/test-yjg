import React from "react";

const SOURCE_COLORS = {
  NYT: "#1a1a1a",
  BBC: "#bb1919",
  CNBC: "#005594",
};

function ArticleCard({ article }) {
  const borderColor = SOURCE_COLORS[article.source] || "#666";

  return (
    <div className="article-card" style={{ borderLeft: `4px solid ${borderColor}` }}>
      <div className="article-header">
        <span className="source-badge" style={{ backgroundColor: borderColor }}>
          {article.source}
        </span>
        <span className="article-time">
          {new Date(article.scraped_at).toLocaleString("ko-KR")}
        </span>
      </div>

      <div className="article-body">
        <div className="article-text">
          <h2 className="article-title">
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              {article.title}
            </a>
          </h2>
          <p className="article-summary">{article.summary}</p>
        </div>

        {article.image && (
          <div className="article-image">
            <img
              src={article.image}
              alt={article.title}
              onError={(e) => {
                e.target.style.display = "none";
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default ArticleCard;
