import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { eventService, bookingService } from '../utils/api';
import '../styles/EventDetail.css';

function EventDetail() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTickets, setSelectedTickets] = useState([]);
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '');
  const [reserving, setReserving] = useState(false);

  useEffect(() => {
    loadEvent();
  }, [eventId]);

  const loadEvent = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await eventService.getEvent(eventId);
      setEvent(data);
    } catch (err) {
      setError('Failed to load event details. Please try again.');
      console.error('Error loading event:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleTicketSelection = (ticket) => {
    if (ticket.status !== 'available') return;

    setSelectedTickets((prev) => {
      const exists = prev.find((t) => t.id === ticket.id);
      if (exists) {
        return prev.filter((t) => t.id !== ticket.id);
      } else {
        return [...prev, ticket];
      }
    });
  };

  const handleReserveTickets = async () => {
    if (!userId.trim()) {
      alert('Please enter a user ID');
      return;
    }

    if (selectedTickets.length === 0) {
      alert('Please select at least one ticket');
      return;
    }

    try {
      setReserving(true);
      const ticketIds = selectedTickets.map((t) => t.id);
      const booking = await bookingService.reserveTickets(
        eventId,
        userId,
        ticketIds
      );

      // Store booking ID for confirmation page
      localStorage.setItem('userId', userId);
      navigate(`/bookings/${booking.id}/confirm`, {
        state: { booking, event },
      });
    } catch (err) {
      const errorMessage =
        err.response?.data?.error || 'Failed to reserve tickets. Please try again.';
      alert(errorMessage);
      console.error('Error reserving tickets:', err);
    } finally {
      setReserving(false);
    }
  };

  const getTotalPrice = () => {
    return selectedTickets.reduce((sum, ticket) => sum + ticket.price, 0);
  };

  const groupTicketsBySection = () => {
    if (!event?.tickets) return {};
    return event.tickets.reduce((acc, ticket) => {
      const key = `${ticket.section}-${ticket.row}`;
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(ticket);
      return acc;
    }, {});
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading event details...</p>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="error-container">
        <p>{error || 'Event not found'}</p>
        <button onClick={() => navigate('/')} className="back-button">
          Back to Events
        </button>
      </div>
    );
  }

  const ticketsBySection = groupTicketsBySection();
  const availableTickets = event.tickets?.filter(
    (t) => t.status === 'available'
  ) || [];

  return (
    <div className="event-detail-page">
      <button onClick={() => navigate('/')} className="back-button">
        ← Back to Events
      </button>

      <div className="event-header">
        {event.image_url && (
          <div className="event-header-image">
            <img src={event.image_url} alt={event.name} />
          </div>
        )}
        <div className="event-header-info">
          <h1>{event.name}</h1>
          <p className="event-description-full">{event.description}</p>
          <div className="event-info-grid">
            <div className="info-item">
              <strong>Type:</strong> {event.event_type}
            </div>
            {event.start_time && (
              <div className="info-item">
                <strong>Date & Time:</strong>{' '}
                {format(new Date(event.start_time), 'EEEE, MMMM dd, yyyy h:mm a')}
              </div>
            )}
            {event.venue && (
              <>
                <div className="info-item">
                  <strong>Venue:</strong> {event.venue.name}
                </div>
                <div className="info-item">
                  <strong>Location:</strong> {event.venue.city}, {event.venue.state}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="ticket-selection-section">
        <div className="selection-header">
          <h2>Select Tickets</h2>
          <div className="user-id-input">
            <label htmlFor="userId">User ID:</label>
            <input
              id="userId"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Enter your user ID"
            />
          </div>
        </div>

        {availableTickets.length === 0 ? (
          <div className="no-tickets">
            <p>No tickets available for this event.</p>
          </div>
        ) : (
          <>
            <div className="tickets-grid">
              {Object.entries(ticketsBySection).map(([key, tickets]) => (
                <div key={key} className="ticket-section">
                  <h3 className="section-title">
                    Section: {tickets[0].section} | Row: {tickets[0].row}
                  </h3>
                  <div className="tickets-row">
                    {tickets.map((ticket) => {
                      const isSelected = selectedTickets.some(
                        (t) => t.id === ticket.id
                      );
                      const isAvailable = ticket.status === 'available';

                      return (
                        <button
                          key={ticket.id}
                          className={`ticket-button ${isSelected ? 'selected' : ''} ${
                            !isAvailable ? 'unavailable' : ''
                          }`}
                          onClick={() => toggleTicketSelection(ticket)}
                          disabled={!isAvailable}
                        >
                          <div className="ticket-seat">{ticket.seat_number}</div>
                          <div className="ticket-price">${ticket.price}</div>
                          <div className="ticket-status">{ticket.status}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            {selectedTickets.length > 0 && (
              <div className="booking-summary">
                <h3>Booking Summary</h3>
                <div className="summary-content">
                  <div className="selected-tickets-list">
                    {selectedTickets.map((ticket) => (
                      <div key={ticket.id} className="summary-ticket">
                        <span>
                          Section {ticket.section}, Row {ticket.row}, Seat{' '}
                          {ticket.seat_number}
                        </span>
                        <span>${ticket.price}</span>
                      </div>
                    ))}
                  </div>
                  <div className="summary-total">
                    <strong>Total: ${getTotalPrice().toFixed(2)}</strong>
                  </div>
                  <button
                    onClick={handleReserveTickets}
                    disabled={reserving}
                    className="reserve-button"
                  >
                    {reserving ? 'Reserving...' : 'Reserve Tickets'}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default EventDetail;

