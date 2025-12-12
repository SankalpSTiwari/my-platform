import React from 'react';
import { format } from 'date-fns';
import './SearchResults.css';

function SearchResults({ results }) {
  if (!results || results.length === 0) {
    return (
      <div className="no-results">
        <p>No results found. Try a different search query.</p>
      </div>
    );
  }

  const getLevelColor = (level) => {
    const colors = {
      ERROR: '#f44336',
      WARN: '#ff9800',
      INFO: '#2196f3',
      DEBUG: '#9e9e9e',
    };
    return colors[level] || '#666';
  };

  return (
    <div className="search-results">
      <h2>Search Results</h2>
      <div className="results-list">
        {results.map((result) => (
          <div key={result.id} className="result-item">
            <div className="result-header">
              <span
                className="result-level"
                style={{ backgroundColor: getLevelColor(result.level) }}
              >
                {result.level || 'LOG'}
              </span>
              <span className="result-source">{result.source || 'unknown'}</span>
              <span className="result-timestamp">
                {format(new Date(result.timestamp), 'yyyy-MM-dd HH:mm:ss')}
              </span>
            </div>
            <div className="result-content">{result.content}</div>
            {result.metadata && Object.keys(result.metadata).length > 0 && (
              <div className="result-metadata">
                {Object.entries(result.metadata).map(([key, value]) => (
                  <span key={key} className="metadata-tag">
                    {key}: {value}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default SearchResults;

