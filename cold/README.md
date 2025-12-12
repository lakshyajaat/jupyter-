# Cold Storage Management System

A modern full-stack cold storage management application with separate frontend and backend.

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Go + PostgreSQL
- **Database**: PostgreSQL (via Docker)
- **Authentication**: JWT tokens with bcrypt password hashing

## Prerequisites

- Docker and Docker Compose
- Go 1.22+
- Node.js 18+

## Quick Start

### 1. Start PostgreSQL

```bash
cd /home/lakshya/jupyter-/cold
make db-up
```

Or manually:
```bash
sudo docker compose up -d
```

### 2. Run Database Migrations

You can either:

**Option A: Use Docker exec (easiest)**
```bash
docker compose exec -T postgres psql -U postgres -d cold_db < cold-backend/migrations/001_create_users.sql
docker compose exec -T postgres psql -U postgres -d cold_db < cold-backend/migrations/002_add_auth_to_users.sql
```

**Option B: Use make (requires psql client)**
```bash
make migrate
```

### 3. Start Backend

In one terminal:
```bash
cd /home/lakshya/jupyter-/cold/cold-backend
go run cmd/server/main.go
```

Or use make:
```bash
make backend
```

Backend will start on: **http://localhost:8080**

### 4. Start Frontend

In another terminal:
```bash
cd /home/lakshya/jupyter-/cold/frontend
npm run dev
```

Or use make:
```bash
make frontend
```

Frontend will start on: **http://localhost:5173**

## Project Structure

```
cold/
├── docker-compose.yml          # PostgreSQL container config
├── Makefile                    # Helpful commands
├── cold-backend/
│   ├── cmd/server/main.go     # Backend entry point
│   ├── internal/
│   │   ├── auth/              # JWT & password handling
│   │   ├── config/            # Configuration loader
│   │   ├── db/                # Database connection
│   │   ├── handlers/          # HTTP request handlers
│   │   ├── http/              # Router setup
│   │   ├── middleware/        # Auth & CORS middleware
│   │   ├── models/            # Data models
│   │   ├── repositories/      # Database queries
│   │   └── services/          # Business logic
│   ├── migrations/            # SQL migrations
│   ├── configs/config.yaml    # App configuration
│   └── .env                   # Environment variables
└── frontend/
    ├── src/
    │   ├── api/               # API client & auth
    │   ├── components/        # React components
    │   ├── pages/             # Page components
    │   └── App.tsx            # Main app with routing
    ├── vite.config.ts         # Vite config with proxy
    └── package.json

```

## API Endpoints

### Public Routes
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Login with email/password

### Protected Routes (require JWT token)
- `POST /users` - Create user (admin)
- `GET /users/{id}` - Get user by ID

## Environment Variables

Backend (`.env`):
```env
JWT_SECRET=your-secret-key
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=cold_db
SERVER_PORT=8080
```

## Development

### Using Make Commands

```bash
make help          # Show all available commands
make db-up         # Start PostgreSQL
make db-down       # Stop PostgreSQL
make db-logs       # View PostgreSQL logs
make migrate       # Run migrations
make backend       # Start backend server
make frontend      # Start frontend server
make dev           # Start database (backend & frontend separately)
make clean         # Stop all services
```

### Manual Commands

**Start PostgreSQL:**
```bash
sudo docker compose up -d
```

**Stop PostgreSQL:**
```bash
sudo docker compose down
```

**View PostgreSQL logs:**
```bash
docker compose logs -f postgres
```

**Access PostgreSQL shell:**
```bash
docker compose exec postgres psql -U postgres -d cold_db
```

## Features

### Frontend
- ✅ User signup and login
- ✅ JWT token storage
- ✅ Protected routes
- ✅ Automatic token refresh
- ✅ Error handling with user feedback
- ✅ Loading states
- ✅ Responsive dashboard

### Backend
- ✅ RESTful API
- ✅ JWT authentication
- ✅ Password hashing with bcrypt
- ✅ CORS configuration
- ✅ Clean architecture
- ✅ PostgreSQL database
- ✅ Environment-based config

## Testing the Application

1. Open http://localhost:5173
2. Click "Sign up" and create an account
3. You'll be automatically logged in and redirected to dashboard
4. Try logging out and logging back in
5. Try accessing /dashboard directly without login (should redirect to login)

## Troubleshooting

### PostgreSQL not starting
```bash
# Check if port 5432 is already in use
sudo lsof -i :5432

# Check Docker status
docker compose ps
docker compose logs postgres
```

### Backend connection errors
```bash
# Verify PostgreSQL is running
docker compose ps

# Check backend can connect
cd cold-backend
go run cmd/server/main.go
```

### Frontend can't reach backend
- Ensure backend is running on port 8080
- Check Vite proxy configuration in `frontend/vite.config.ts`
- Check browser console for CORS errors

### Migrations not running
```bash
# Run migrations manually
docker compose exec -T postgres psql -U postgres -d cold_db < cold-backend/migrations/001_create_users.sql
docker compose exec -T postgres psql -U postgres -d cold_db < cold-backend/migrations/002_add_auth_to_users.sql
```

## Next Steps

- [ ] Add more storage management features
- [ ] Implement role-based access control
- [ ] Add inventory management
- [ ] Add temperature monitoring
- [ ] Create admin dashboard
- [ ] Add reporting features

## License

MIT
