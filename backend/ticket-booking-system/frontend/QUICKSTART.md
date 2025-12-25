# Quick Start Guide

## Prerequisites

1. **Backend API** must be running. See the main README for backend setup.
2. **Node.js 16+** and **npm** installed

## Setup Steps

1. **Navigate to the frontend directory:**
   ```bash
   cd backend/ticket-booking-system/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

   The app will open at `http://localhost:3000`

4. **Make sure the backend is running:**
   ```bash
   # In another terminal, from backend/ticket-booking-system
   export PYTHONPATH=src
   export API_PORT=5000
   python -m ticketbooking.main
   ```

## Using the Application

1. **Browse Events**: The home page shows all available events. Use the search bar to filter by keyword, city, or event type.

2. **View Event Details**: Click on any event card to see full details including venue information.

3. **Select Tickets**: On the event detail page, click on available tickets to select them. Selected tickets will be highlighted.

4. **Reserve Tickets**: Enter your user ID and click "Reserve Tickets" to hold your selected tickets.

5. **Confirm Booking**: On the confirmation page, enter a payment ID and confirm your booking.

## Troubleshooting

- **API Connection Issues**: Make sure the backend is running on port 5000 (or update the proxy in `package.json`)
- **CORS Errors**: The backend has CORS enabled, but if you see errors, check that the backend is running and accessible
- **No Events Showing**: Make sure the database has been seeded with event data

## Customization

- **API URL**: Set `REACT_APP_API_URL` environment variable to change the API endpoint
- **Port**: The frontend runs on port 3000 by default (React's default)
- **Styling**: All styles are in the `src/styles/` directory and can be customized

