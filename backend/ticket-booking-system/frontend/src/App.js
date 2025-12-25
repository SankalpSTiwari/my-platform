import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './styles/App.css';
import EventList from './pages/EventList';
import EventDetail from './pages/EventDetail';
import BookingConfirmation from './pages/BookingConfirmation';

function App() {
  return (
    <Router>
      <div className='App'>
        <header className='app-header'>
          <Link to='/' className='logo'>
            <h1>🎫 Ticket Booking</h1>
          </Link>
          <nav>
            <Link to='/'>Events</Link>
          </nav>
        </header>

        <main className='app-main'>
          <Routes>
            <Route path='/' element={<EventList />} />
            <Route path='/events/:eventId' element={<EventDetail />} />
            <Route
              path='/bookings/:bookingId/confirm'
              element={<BookingConfirmation />}
            />
          </Routes>
        </main>

        <footer className='app-footer'>
          <p>&copy; 2024 Ticket Booking System. All rights reserved.</p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
