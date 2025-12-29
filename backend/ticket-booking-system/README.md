# Ticket Booking System

A scalable event ticketing platform inspired by Ticketmaster, designed to handle high-traffic events with millions of concurrent users.

## Features

- **Event Management**: View and search events with filtering capabilities
- **Ticket Booking**: Reserve and purchase tickets with distributed locking to prevent double bookings
- **Real-time Availability**: Check ticket availability in real-time
- **Scalable Architecture**: Designed for high read throughput (100:1 read/write ratio)
- **ACID Transactions**: Ensures data consistency for ticket purchases

## Architecture

### Core Entities

- **Event**: Stores event information (name, description, type, date, venue, performer)
- **Venue**: Physical location details (address, capacity, seat map)
- **Performer**: Artist, team, or group performing at the event
- **Ticket**: Individual ticket with seat details, pricing, and status
- **Booking**: Transaction record linking user, tickets, and payment

### System Components

#### 1. Event Service
- Handles viewing and searching events
- Provides event details with venue and performer information
- Supports keyword search, date filtering, and location-based queries

#### 2. Booking Service
- Manages ticket reservations using distributed locks (Redis)
- Handles booking confirmation after payment
- Prevents double bookings using ACID transactions and row-level locking
- Implements reservation timeout (default: 10 minutes)

#### 3. Ticket Service
- Manages ticket availability and status
- Provides seat map data for event pages

### API Endpoints

#### View Event
```
GET /api/events/:eventId
```
Returns event details including venue, performer, and available tickets.

#### Search Events
```
GET /api/events/search?keyword={keyword}&start={start_date}&end={end_date}&pageSize={page_size}&page={page_number}
```
Returns a list of events matching the search criteria.

#### Reserve Tickets
```
POST /api/bookings/:eventId
Body: {
  "userId": "user123",
  "ticketIds": ["ticket1", "ticket2"]
}
```
Reserves tickets for a user for a limited time (10 minutes by default).

#### Confirm Booking
```
POST /api/bookings/:bookingId/confirm
Body: {
  "paymentId": "payment123"
}
```
Confirms a booking after successful payment processing.

## Database Schema

The system uses PostgreSQL with the following main tables:

- `events`: Event information
- `venues`: Venue details and seat maps
- `performers`: Performer/artist information
- `tickets`: Individual ticket records
- `bookings`: Booking transactions
- `event_performer`: Many-to-many relationship between events and performers

## Quickstart

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (for distributed locking)

### Installation

1. Install dependencies:
```bash
make install
# or
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost/ticketbooking"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export API_PORT="5000"
```

3. Initialize database:
```bash
make db-init
# or
export PYTHONPATH=src
python -c "from ticketbooking.api.server import init_db; from ticketbooking.config import Config; init_db(Config.from_env().database_url)"
```

4. Run the server:
```bash
make run
# or
export PYTHONPATH=src
python -m ticketbooking.main
```

The server will start on `http://localhost:5000` (or the port specified in `API_PORT`).

## Configuration

Environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 5000)
- `REDIS_HOST`: Redis host (default: localhost)
- `REDIS_PORT`: Redis port (default: 6379)
- `BOOKING_LOCK_TTL_SECONDS`: Reservation timeout in seconds (default: 600)
- `CACHE_TTL_SECONDS`: Cache TTL for event data (default: 300)
- `SEARCH_PAGE_SIZE`: Default page size for search results (default: 20)

## Key Design Decisions

### Preventing Double Bookings

1. **Distributed Locking**: Uses Redis to lock tickets during reservation
2. **Database Transactions**: PostgreSQL transactions with row-level locking (`FOR UPDATE`)
3. **Optimistic Concurrency Control**: Status checks before confirming bookings
4. **Reservation Timeout**: Automatic release of reserved tickets after timeout

### Scalability Considerations

- **Read-Heavy Workload**: Optimized for high read throughput (100:1 ratio)
- **Caching**: Event data can be cached (Redis/CDN) for popular events
- **Horizontal Scaling**: Stateless API services can be scaled horizontally
- **Database Sharding**: Can shard by event_id or venue_id for very high scale

### Future Enhancements

- Elasticsearch integration for advanced search capabilities
- Real-time seat map updates using WebSockets or Server-Sent Events
- Virtual waiting room for high-demand events
- Payment webhook integration (Stripe, PayPal, etc.)
- Event caching with Redis/CDN
- Search result caching

## Testing

Run tests:
```bash
make test
```

With coverage:
```bash
make test-cov
```

## Project Structure

```
ticket-booking-system/
├── src/
│   └── ticketbooking/
│       ├── __init__.py
│       ├── config.py          # Configuration management
│       ├── main.py             # Entry point
│       ├── api/
│       │   ├── __init__.py
│       │   └── server.py       # Flask API endpoints
│       ├── models/
│       │   ├── __init__.py
│       │   ├── entities.py     # Domain entities
│       │   └── database.py     # SQLAlchemy models
│       └── services/
│           ├── __init__.py
│           ├── event_service.py
│           ├── booking_service.py
│           └── ticket_service.py
├── tests/                      # Unit tests
├── docs/                       # Documentation
├── requirements.txt
├── Makefile
└── README.md
```

## API Usage Examples

### View an Event
```bash
curl http://localhost:5000/api/events/event123
```

### Search Events
```bash
curl "http://localhost:5000/api/events/search?keyword=concert&city=San+Francisco&pageSize=20"
```

### Reserve Tickets
```bash
curl -X POST http://localhost:5000/api/bookings/event123 \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user123",
    "ticketIds": ["ticket1", "ticket2"]
  }'
```

### Confirm Booking
```bash
curl -X POST http://localhost:5000/api/bookings/booking123/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "paymentId": "payment123"
  }'
```

## License

MIT




