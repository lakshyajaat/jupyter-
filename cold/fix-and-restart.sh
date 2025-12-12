#!/bin/bash

echo "🔧 Fixing Cold Storage System..."
echo ""

cd /home/lakshya/jupyter-/cold/cold-backend

echo "1️⃣ Running database migrations..."
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/001_create_users.sql 2>&1 | grep -v "already exists" | grep -v "ERROR.*already exists" || true
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/002_add_auth_to_users.sql 2>&1 | grep -v "already exists" | grep -v "ERROR.*already exists" || true
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/003_seed_admin_user.sql 2>&1 | grep -v "duplicate" | grep -v "ERROR.*duplicate" || true
sudo docker exec -i cold-storage-postgres psql -U postgres -d cold_db < migrations/004_add_role_to_users.sql 2>&1 | grep -v "already exists" | grep -v "ERROR.*already exists" || true

echo ""
echo "2️⃣ Verifying admin user with role..."
sudo docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT id, name, email, role FROM users WHERE email = 'admin@cold.com';"

echo ""
echo "3️⃣ Stopping old backend..."
pkill -f "go run cmd/server/main.go" 2>/dev/null || true
sleep 2

echo ""
echo "4️⃣ Starting new backend..."
nohup go run cmd/server/main.go > /tmp/cold-backend.log 2>&1 &
sleep 3

echo ""
echo "5️⃣ Verifying backend is running..."
if netstat -tuln | grep -q ":8080"; then
    echo "✅ Backend running on port 8080!"
else
    echo "❌ Backend failed. Check logs: tail -f /tmp/cold-backend.log"
    exit 1
fi

echo ""
echo "6️⃣ Testing new routes..."
echo "   /logout - $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/logout)"
echo "   /room-config-1 - $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/room-config-1)"
echo "   /admin/dashboard - $(curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/admin/dashboard)"

echo ""
echo "✅ All fixes applied!"
echo ""
echo "🌐 Access:"
echo "   http://localhost:8080"
echo "   http://192.168.15.195:8080"
echo ""
echo "🔑 Login as admin:"
echo "   Email: admin@cold.com"
echo "   Password: admin123"
echo "   → Will redirect to ADMIN dashboard"
echo ""
echo "📋 Backend logs:"
echo "   tail -f /tmp/cold-backend.log"
