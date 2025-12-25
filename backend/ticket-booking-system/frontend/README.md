# Ticket Booking System - Frontend

A modern React frontend for the Ticket Booking System, providing an intuitive interface for browsing events, selecting tickets, and completing bookings.

## Features

- **Event Browsing**: Search and filter events by keyword, city, type, and date
- **Event Details**: View comprehensive event information including venue and performer details
- **Ticket Selection**: Interactive seat map with real-time availability
- **Booking Flow**: Reserve tickets and confirm bookings with payment integration
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Prerequisites

- Node.js 16+ and npm
- Backend API running on port 5000 (or configure via environment variable)

## Installation

1. Install dependencies:
```bash
npm install
```

2. Configure API URL (optional):
Create a `.env` file in the frontend directory:
```
REACT_APP_API_URL=http://localhost:5000
```

## Running the Application

1. Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

2. Make sure the backend API is running on port 5000 (or the configured port).

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build` folder.

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/         # Reusable components
│   ├── pages/              # Page components
│   │   ├── EventList.js    # Event browsing/search page
│   │   ├── EventDetail.js  # Event details and ticket selection
│   │   └── BookingConfirmation.js  # Booking confirmation page
│   ├── styles/             # CSS files
│   ├── utils/              # Utility functions
│   │   └── api.js          # API service functions
│   ├── App.js              # Main app component with routing
│   └── index.js            # Entry point
├── package.json
└── README.md
```

## API Integration

The frontend communicates with the backend API through the `api.js` utility:

- `eventService.getEvent(eventId)` - Get event details
- `eventService.searchEvents(params)` - Search events
- `bookingService.reserveTickets(eventId, userId, ticketIds)` - Reserve tickets
- `bookingService.confirmBooking(bookingId, paymentId)` - Confirm booking

## Features in Detail

### Event List Page
- Search events by keyword, city, and event type
- Display events in a responsive grid layout
- Click on any event to view details

### Event Detail Page
- View complete event information
- Select available tickets from the seat map
- See real-time pricing and availability
- Reserve selected tickets

### Booking Confirmation Page
- Review booking summary
- Enter payment information
- Confirm booking to complete the transaction

## Styling

The application uses modern CSS with:
- Gradient backgrounds
- Smooth transitions and animations
- Responsive grid layouts
- Mobile-first design approach

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

The app uses React Router for navigation and Axios for API calls. The proxy configuration in `package.json` allows API calls to be made to the backend during development.

