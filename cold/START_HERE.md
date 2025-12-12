# 🚀 Quick Start Guide

Follow these steps to get your Cold Storage app running:

## Step 1: Start PostgreSQL Database

```bash
cd /home/lakshya/jupyter-/cold
sudo docker compose up -d
```

Wait a few seconds for PostgreSQL to start, then verify:
```bash
docker compose ps
```

## Step 2: Run Database Migrations

```bash
docker compose exec -T postgres psql -U postgres -d cold_db < cold-backend/migrations/001_create_users.sql
docker compose exec -T postgres psql -U postgres -d cold_db < cold-backend/migrations/002_add_auth_to_users.sql
```

## Step 3: Start Backend Server

Open a new terminal:
```bash
cd /home/lakshya/jupyter-/cold/cold-backend
go run cmd/server/main.go
```

You should see: `Server running on :8080`

## Step 4: Start Frontend Dev Server

Open another terminal:
```bash
cd /home/lakshya/jupyter-/cold/frontend
npm run dev
```

You should see Vite dev server running on port 5173

## Step 5: Test the Application

**Access locally:**
1. Open http://localhost:5173 in your browser

**Access from network (other devices):**
1. Open http://192.168.15.195:5173 in your browser
2. Or use your machine's IP address

Then:
1. Click "Don't have an account? Sign up"
2. Create a new account
3. You'll be automatically logged in
4. Try logging out and logging back in

## Done! 🎉

Your Cold Storage Management System is now running!

- Frontend: http://localhost:5173 (or http://192.168.15.195:5173)
- Backend API: http://localhost:8080 (or http://192.168.15.195:8080)
- Database: PostgreSQL on port 5432

**Note:** If accessing from another device on your network, make sure both devices are on the same network!

## Stopping Everything

```bash
# Stop backend & frontend: Press Ctrl+C in their terminals

# Stop database:
cd /home/lakshya/jupyter-/cold
docker compose down
```

## Need Help?

See the full README.md for detailed documentation and troubleshooting.
