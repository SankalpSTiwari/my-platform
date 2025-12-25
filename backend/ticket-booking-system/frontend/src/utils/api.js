import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5002';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const eventService = {
  getEvent: async (eventId) => {
    const response = await api.get(`/api/events/${eventId}`);
    return response.data;
  },

  searchEvents: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.keyword) queryParams.append('keyword', params.keyword);
    if (params.start) queryParams.append('start', params.start);
    if (params.end) queryParams.append('end', params.end);
    if (params.event_type) queryParams.append('event_type', params.event_type);
    if (params.city) queryParams.append('city', params.city);
    if (params.page) queryParams.append('page', params.page);
    if (params.pageSize) queryParams.append('pageSize', params.pageSize);

    const response = await api.get(`/api/events/search?${queryParams.toString()}`);
    return response.data;
  },
};

export const bookingService = {
  reserveTickets: async (eventId, userId, ticketIds) => {
    const response = await api.post(`/api/bookings/${eventId}`, {
      userId,
      ticketIds,
    });
    return response.data;
  },

  confirmBooking: async (bookingId, paymentId) => {
    const response = await api.post(`/api/bookings/${bookingId}/confirm`, {
      paymentId,
    });
    return response.data;
  },
};

export default api;

