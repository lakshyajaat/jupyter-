.PHONY: help db-up db-down db-logs migrate backend frontend dev clean

help:
	@echo "Available commands:"
	@echo "  make db-up       - Start PostgreSQL with Docker"
	@echo "  make db-down     - Stop PostgreSQL"
	@echo "  make db-logs     - View PostgreSQL logs"
	@echo "  make migrate     - Run database migrations"
	@echo "  make backend     - Start Go backend server"
	@echo "  make frontend    - Start React frontend dev server"
	@echo "  make dev         - Start both backend and frontend"
	@echo "  make clean       - Stop all services"

db-up:
	docker compose up -d
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	@docker compose exec -T postgres pg_isready -U postgres

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

migrate:
	@echo "Running migrations..."
	@cd cold-backend && bash scripts/migrate.sh

backend:
	cd cold-backend && go run cmd/server/main.go

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting all services..."
	@make db-up
	@echo ""
	@echo "==================================="
	@echo "Start backend in one terminal:    make backend"
	@echo "Start frontend in another:        make frontend"
	@echo "==================================="

clean:
	@make db-down
	@pkill -f "go run cmd/server/main.go" || true
	@pkill -f "vite" || true
	@echo "All services stopped"
