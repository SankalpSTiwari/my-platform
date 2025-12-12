import React, { useState } from 'react';
import './LogIngest.css';

function LogIngest() {
  const [message, setMessage] = useState('');
  const [level, setLevel] = useState('INFO');
  const [source, setSource] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    setStatus(null);

    try {
      const response = await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          level,
          source: source || 'web-ui',
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to ingest log');
      }

      setStatus({ type: 'success', message: 'Log ingested successfully!' });
      setMessage('');
    } catch (err) {
      setStatus({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="log-ingest">
      <h3>Ingest Log</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Message:</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter log message..."
            rows={4}
            disabled={loading}
            required
          />
        </div>

        <div className="form-group">
          <label>Level:</label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value)}
            disabled={loading}
          >
            <option value="DEBUG">DEBUG</option>
            <option value="INFO">INFO</option>
            <option value="WARN">WARN</option>
            <option value="ERROR">ERROR</option>
          </select>
        </div>

        <div className="form-group">
          <label>Source:</label>
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="Optional source identifier"
            disabled={loading}
          />
        </div>

        <button type="submit" className="ingest-button" disabled={loading || !message.trim()}>
          {loading ? 'Ingesting...' : 'Ingest Log'}
        </button>

        {status && (
          <div className={`status-message ${status.type}`}>
            {status.message}
          </div>
        )}
      </form>
    </div>
  );
}

export default LogIngest;

