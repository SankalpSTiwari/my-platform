import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { format } from 'date-fns';
import { bookingService } from '../utils/api';
import '../styles/BookingConfirmation.css';

function BookingConfirmation() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [booking, setBooking] = useState(location.state?.booking || null);
  const [event, setEvent] = useState(location.state?.event || null);
  const [paymentId, setPaymentId] = useState('');
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!booking || !event) {
      // If we don't have booking/event from navigation state, redirect
      navigate('/');
    }
  }, [booking, event, navigate]);

  const handleConfirmBooking = async () => {
    if (!paymentId.trim()) {
      alert('Please enter a payment ID');
      return;
    }

    try {
      setConfirming(true);
      setError(null);
      const confirmedBooking = await bookingService.confirmBooking(
        bookingId,
        paymentId
      );
      setBooking(confirmedBooking);
      setConfirmed(true);
    } catch (err) {
      const errorMessage =
        err.response?.data?.error || 'Failed to confirm booking. Please try again.';
      setError(errorMessage);
      console.error('Error confirming booking:', err);
    } finally {
      setConfirming(false);
    }
  };

  if (!booking || !event) {
    return null;
  }

  return (
    <div className="booking-confirmation-page">
      <div className="confirmation-container">
        {confirmed ? (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h1>Booking Confirmed!</h1>
            <p>Your tickets have been successfully reserved.</p>
            <div className="booking-details">
              <h2>Booking Details</h2>
              <div className="detail-item">
                <strong>Booking ID:</strong> {booking.id}
              </div>
              <div className="detail-item">
                <strong>Event:</strong> {event.name}
              </div>
              <div className="detail-item">
                <strong>Total Price:</strong> ${booking.totalPrice.toFixed(2)}
              </div>
              <div className="detail-item">
                <strong>Status:</strong> {booking.status}
              </div>
              {booking.confirmedAt && (
                <div className="detail-item">
                  <strong>Confirmed At:</strong>{' '}
                  {format(new Date(booking.confirmedAt), 'MMM dd, yyyy h:mm a')}
                </div>
              )}
              {booking.paymentId && (
                <div className="detail-item">
                  <strong>Payment ID:</strong> {booking.paymentId}
                </div>
              )}
            </div>
            <button onClick={() => navigate('/')} className="home-button">
              Back to Events
            </button>
          </div>
        ) : (
          <>
            <h1>Confirm Your Booking</h1>
            <div className="booking-info">
              <h2>{event.name}</h2>
              <div className="info-section">
                <h3>Booking Summary</h3>
                <div className="summary-item">
                  <strong>Booking ID:</strong> {booking.id}
                </div>
                <div className="summary-item">
                  <strong>Total Price:</strong> ${booking.totalPrice.toFixed(2)}
                </div>
                <div className="summary-item">
                  <strong>Tickets Reserved:</strong> {booking.ticketIds?.length || 0}
                </div>
                {booking.expiresAt && (
                  <div className="summary-item">
                    <strong>Reservation Expires:</strong>{' '}
                    {format(new Date(booking.expiresAt), 'MMM dd, yyyy h:mm a')}
                  </div>
                )}
              </div>

              <div className="payment-section">
                <h3>Payment Information</h3>
                <div className="payment-input">
                  <label htmlFor="paymentId">Payment ID:</label>
                  <input
                    id="paymentId"
                    type="text"
                    value={paymentId}
                    onChange={(e) => setPaymentId(e.target.value)}
                    placeholder="Enter payment ID"
                  />
                  <small>
                    In a real application, this would be handled by a payment
                    gateway (Stripe, PayPal, etc.)
                  </small>
                </div>
              </div>

              {error && (
                <div className="error-message">
                  <p>{error}</p>
                </div>
              )}

              <div className="action-buttons">
                <button
                  onClick={() => navigate('/')}
                  className="cancel-button"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirmBooking}
                  disabled={confirming || !paymentId.trim()}
                  className="confirm-button"
                >
                  {confirming ? 'Confirming...' : 'Confirm Booking'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default BookingConfirmation;

