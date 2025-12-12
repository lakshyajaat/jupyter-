#!/bin/bash

echo "🔧 Creating admin user..."

docker exec cold-storage-postgres psql -U postgres -d cold_db -c "
INSERT INTO users (name, email, password_hash, created_at, updated_at)
VALUES (
    'Administrator',
    'admin@cold.com',
    '\$2a\$12\$eva1KcgmhwYUwDTOHQmyt.KZmPfAhvJuqbHIVLTzNbqSFISKqf8s6',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE SET
    password_hash = '\$2a\$12\$eva1KcgmhwYUwDTOHQmyt.KZmPfAhvJuqbHIVLTzNbqSFISKqf8s6',
    updated_at = CURRENT_TIMESTAMP;
"

echo ""
echo "✅ Admin user created/updated!"
echo ""
echo "🔍 Verifying admin user exists:"
docker exec cold-storage-postgres psql -U postgres -d cold_db -c "SELECT id, name, email, created_at FROM users WHERE email = 'admin@cold.com';"

echo ""
echo "✅ Done! Now try logging in with:"
echo "   Email: admin@cold.com"
echo "   Password: admin123"
