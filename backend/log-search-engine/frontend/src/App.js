import React, { useState } from 'react';
import './App.css';
import SearchBar from './components/SearchBar';
import SearchResults from './components/SearchResults';
import AggregationsChart from './components/AggregationsChart';
import LogIngest from './components/LogIngest';

function App() {
  const [searchResults, setSearchResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (query, startTime, endTime) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          start_time: startTime,
          end_time: endTime,
          limit: 100,
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setSearchResults(data);
    } catch (err) {
      setError(err.message);
      setSearchResults(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔍 Log Search Engine</h1>
        <p>Full-text search with inverted index, time-based partitioning, and aggregations</p>
      </header>

      <div className="App-container">
        <div className="App-sidebar">
          <LogIngest />
        </div>

        <div className="App-main">
          <SearchBar onSearch={handleSearch} loading={loading} />
          
          {error && (
            <div className="error-message">
              Error: {error}
            </div>
          )}

          {searchResults && (
            <>
              <div className="search-stats">
                <p>
                  Found {searchResults.total_count} results 
                  ({searchResults.returned_count} shown) 
                  in {searchResults.execution_time_ms}ms
                </p>
              </div>

              {searchResults.aggregations && (
                <AggregationsChart aggregations={searchResults.aggregations} />
              )}

              <SearchResults results={searchResults.results} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;

