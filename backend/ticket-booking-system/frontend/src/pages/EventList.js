import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { eventService } from '../utils/api';
import '../styles/EventList.css';

function EventList() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchParams, setSearchParams] = useState({
    keyword: '',
    city: '',
    event_type: '',
    start: '',
    end: '',
  });

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await eventService.searchEvents(searchParams);
      setEvents(data);
    } catch (err) {
      setError('Failed to load events. Please try again.');
      console.error('Error loading events:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadEvents();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSearchParams((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading events...</p>
      </div>
    );
  }

  return (
    <div className="event-list-page">
      <div className="page-header">
        <h2>Discover Events</h2>
        <p>Find and book tickets for your favorite events</p>
      </div>

      <div className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-row">
            <input
              type="text"
              name="keyword"
              placeholder="Search events..."
              value={searchParams.keyword}
              onChange={handleInputChange}
              className="search-input"
            />
            <input
              type="text"
              name="city"
              placeholder="City"
              value={searchParams.city}
              onChange={handleInputChange}
              className="search-input"
            />
            <select
              name="event_type"
              value={searchParams.event_type}
              onChange={handleInputChange}
              className="search-select"
            >
              <option value="">All Types</option>
              <option value="concert">Concert</option>
              <option value="sports">Sports</option>
              <option value="theater">Theater</option>
              <option value="comedy">Comedy</option>
              <option value="festival">Festival</option>
            </select>
            <button type="submit" className="search-button">
              Search
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      {events.length === 0 && !loading ? (
        <div className="no-events">
          <p>No events found. Try adjusting your search criteria.</p>
        </div>
      ) : (
        <div className="events-grid">
          {events.map((event) => (
            <Link
              key={event.id}
              to={`/events/${event.id}`}
              className="event-card"
            >
              {event.image_url && (
                <div className="event-image">
                  <img src={event.image_url} alt={event.name} />
                </div>
              )}
              <div className="event-content">
                <h3 className="event-name">{event.name}</h3>
                <p className="event-description">
                  {event.description?.substring(0, 100)}
                  {event.description?.length > 100 ? '...' : ''}
                </p>
                <div className="event-meta">
                  <span className="event-type">{event.event_type}</span>
                  {event.start_time && (
                    <span className="event-date">
                      {format(new Date(event.start_time), 'MMM dd, yyyy h:mm a')}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default EventList;

