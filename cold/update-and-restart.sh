#!/bin/bash

echo "🔄 Updating Cold Storage System..."
echo ""

echo "1️⃣ Running all database migrations..."
cd /home/lakshya/jupyter-/cold/cold-backend

sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/001_create_users.sql 2>&1 | grep -v "already exists" || true
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/002_add_auth_to_users.sql 2>&1 | grep -v "already exists" || true
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/003_seed_admin_user.sql 2>&1 | grep -v "duplicate" || true
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/004_add_role_to_users.sql 2>&1 | grep -v "already exists" || true

echo ""
echo "2️⃣ Verifying admin user..."
sudo docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT id, name, email, role FROM users WHERE email = 'admin@cold.com';"

echo ""
echo "3️⃣ Stopping old backend process..."
pkill -f "go run cmd/server/main.go" 2>/dev/null || true
sleep 2

echo ""
echo "4️⃣ Starting new backend..."
cd /home/lakshya/jupyter-/cold/cold-backend
nohup go run cmd/server/main.go > /tmp/cold-backend.log 2>&1 &
sleep 3

echo ""
echo "5️⃣ Checking if backend is running..."
if netstat -tuln | grep -q ":8080"; then
    echo "✅ Backend is running on port 8080!"
else
    echo "❌ Backend failed to start. Check logs:"
    echo "   tail -f /tmp/cold-backend.log"
    exit 1
fi

echo ""
echo "✅ Update complete!"
echo ""
echo "🌐 Access the application:"
echo "   http://localhost:8080"
echo "   http://192.168.15.195:8080"
echo ""
echo "🔑 Login credentials:"
echo "   Email: admin@cold.com"
echo "   Password: admin123"
echo "   Role: admin (will redirect to admin dashboard)"
echo ""
echo "📋 View backend logs:"
echo "   tail -f /tmp/cold-backend.log"
