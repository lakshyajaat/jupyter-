#!/bin/bash

echo "🔍 Checking if admin user exists..."
ADMIN_EXISTS=$(docker exec cold-storage-postgres psql -U postgres -d cold_db -t -c "SELECT COUNT(*) FROM users WHERE email = 'admin@cold.com';")

if [ "$ADMIN_EXISTS" -eq "1" ]; then
    echo "✅ Admin user exists!"
    echo ""
    echo "Credentials:"
    echo "  Email: admin@cold.com"
    echo "  Password: admin123"
else
    echo "❌ Admin user NOT found!"
    echo ""
    echo "Creating admin user now..."
    docker exec -i cold-storage-postgres psql -U postgres -d cold_db < cold-backend/migrations/003_seed_admin_user.sql
    echo "✅ Admin user created!"
    echo ""
    echo "Credentials:"
    echo "  Email: admin@cold.com"
    echo "  Password: admin123"
fi

echo ""
echo "📊 All users in database:"
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT id, name, email, created_at FROM users;"
