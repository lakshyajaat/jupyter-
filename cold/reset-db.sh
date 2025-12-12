#!/bin/bash

echo "🗑️  Resetting database (dropping all tables)..."
docker exec -i cold-storage-postgres psql -U postgres -d cold_db < cold-backend/migrations/000_reset.sql

echo "✅ Database reset complete!"
echo ""
echo "📦 Running fresh migrations..."

docker exec -i cold-storage-postgres psql -U postgres -d cold_db < cold-backend/migrations/001_create_users.sql
docker exec -i cold-storage-postgres psql -U postgres -d cold_db < cold-backend/migrations/002_add_auth_to_users.sql
docker exec -i cold-storage-postgres psql -U postgres -d cold_db < cold-backend/migrations/003_seed_admin_user.sql

echo ""
echo "✅ Fresh database ready!"
echo ""
echo "🔑 Default Admin Credentials:"
echo "   Email: admin@cold.com"
echo "   Password: admin123"
echo ""
echo "🎉 You can now start the servers and login!"
