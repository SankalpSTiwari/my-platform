import React, { useState } from 'react';
import './SearchBar.css';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    const start = startTime ? new Date(startTime).getTime() : null;
    const end = endTime ? new Date(endTime).getTime() : null;

    onSearch(query, start, end);
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-input-group">
        <input
          type="text"
          className="search-input"
          placeholder="Search logs... (e.g., 'error', 'level:ERROR', 'error | group by level')"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="search-button" disabled={loading || !query.trim()}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      <div className="time-filters">
        <div className="time-filter">
          <label>Start Time:</label>
          <input
            type="datetime-local"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="time-filter">
          <label>End Time:</label>
          <input
            type="datetime-local"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            disabled={loading}
          />
        </div>
      </div>

      <div className="query-examples">
        <p>Query Examples:</p>
        <ul>
          <li><code>error</code> - Simple text search</li>
          <li><code>level:ERROR AND message:timeout</code> - Field filters</li>
          <li><code>error | group by level</code> - With aggregation</li>
        </ul>
      </div>
    </form>
  );
}

export default SearchBar;

