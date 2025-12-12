#!/bin/bash

echo "🔍 Testing Database Connection..."
echo ""

echo "1️⃣ Checking if users table exists..."
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "\dt users"

echo ""
echo "2️⃣ Checking table structure..."
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "\d users"

echo ""
echo "3️⃣ Counting users in database..."
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT COUNT(*) as user_count FROM users;"

echo ""
echo "4️⃣ Showing all users..."
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT id, name, email, LEFT(password_hash, 20) as password_prefix, created_at FROM users;"

echo ""
echo "5️⃣ Inserting admin user (if not exists)..."
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "INSERT INTO users (name, email, password_hash, created_at, updated_at) VALUES ('Administrator', 'admin@cold.com', '\$2a\$12\$eva1KcgmhwYUwDTOHQmyt.KZmPfAhvJuqbHIVLTzNbqSFISKqf8s6', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP) ON CONFLICT (email) DO NOTHING;"

echo ""
echo "6️⃣ Final check - admin user:"
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT id, name, email, created_at FROM users WHERE email = 'admin@cold.com';"

echo ""
echo "✅ Done! Try logging in with:"
echo "   Email: admin@cold.com"
echo "   Password: admin123"
