# 🚀 Cold Storage Management System - Quick Start

## ✅ What Changed?

- ❌ Removed React frontend
- ✅ Added beautiful Neubrutalism HTML templates from go_learning
- ✅ Backend now serves HTML pages AND API endpoints
- ✅ All templates integrated with PostgreSQL backend

## 🎯 Start the Application

### Step 1: Ensure PostgreSQL is Running

```bash
docker compose ps
```

If not running:
```bash
cd /home/lakshya/jupyter-/cold
docker compose up -d
```

### Step 2: Reset Database (Fresh Start)

```bash
cd /home/lakshya/jupyter-/cold
./test-db.sh
```

This will:
- Check database connection
- Create admin user automatically
- Show all users

### Step 3: Start the Backend

```bash
cd /home/lakshya/jupyter-/cold/cold-backend
go run cmd/server/main.go
```

You should see: `Server running on :8080`

### Step 4: Open in Browser

**Local access:**
```
http://localhost:8080
```

**Network access:**
```
http://192.168.15.195:8080
```

## 🔑 Login Credentials

```
Email: admin@cold.com
Password: admin123
```

## 📋 Available Pages

Once logged in, you have access to:

- `/dashboard` - Employee/Admin Dashboard
- `/admin/dashboard` - Admin Dashboard
- `/item-search` - Search Items
- `/events` - Event Tracer
- `/entry-room` - Entry Room Management
- `/main-entry` - Main Entry
- `/room-form-1` - Room Form 1
- `/room-form-2` - Room Form 2
- `/loading-invoice` - Loading Invoice

## 🛠️ Troubleshooting

### Login not working?

1. **Run database fix:**
   ```bash
   cd /home/lakshya/jupyter-/cold
   ./test-db.sh
   ```

2. **Check backend is running:**
   ```bash
   curl http://localhost:8080/login
   ```
   Should show the login HTML page

3. **Test API directly:**
   ```bash
   curl -X POST http://localhost:8080/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@cold.com","password":"admin123"}'
   ```
   Should return a JWT token

### Backend won't start?

```bash
cd /home/lakshya/jupyter-/cold/cold-backend
go mod tidy
go run cmd/server/main.go
```

### PostgreSQL not running?

```bash
cd /home/lakshya/jupyter-/cold
docker compose up -d
docker compose logs -f postgres
```

## 🎨 Features

- ✅ Beautiful Neubrutalism Design
- ✅ Responsive Layout
- ✅ JWT Authentication
- ✅ PostgreSQL Database
- ✅ Session Management
- ✅ All Cold Storage Management Features

## 🗂️ Project Structure

```
cold/
├── docker-compose.yml          # PostgreSQL container
├── cold-backend/
│   ├── cmd/server/main.go     # Server entry point
│   ├── internal/
│   │   ├── handlers/
│   │   │   ├── auth_handler.go      # API auth endpoints
│   │   │   ├── page_handler.go      # HTML page routes
│   │   │   └── user_handler.go
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── middleware/
│   │   └── models/
│   ├── templates/             # HTML templates
│   │   ├── user_login.html
│   │   ├── dashboard_employee.html
│   │   ├── dashboard_admin.html
│   │   └── ...
│   ├── static/                # CSS, JS, images
│   └── migrations/            # SQL migrations
└── frontend/                  # OLD - Not used anymore

```

## 📡 API Endpoints

### HTML Pages (GET)
- `GET /` - Login page
- `GET /login` - Login page
- `GET /dashboard` - Dashboard
- `GET /admin/dashboard` - Admin dashboard
- `GET /item-search` - Item search
- (and more...)

### API Endpoints (JSON)
- `POST /auth/login` - Login API
- `POST /auth/signup` - Signup API
- `GET /users/{id}` - Get user (requires JWT)
- `POST /users` - Create user (requires JWT)

## 🔒 Security Note

⚠️ **Important:** Change the default admin password in production!

The current setup is for development only. Before deploying to production:
1. Change admin password
2. Update JWT secret
3. Enable HTTPS
4. Review CORS settings

---

**Enjoy your Cold Storage Management System! ❄️**
