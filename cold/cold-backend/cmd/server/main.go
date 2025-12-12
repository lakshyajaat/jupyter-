package main

import (
	"fmt"
	"log"
	"net/http"

	"cold-backend/internal/auth"
	"cold-backend/internal/config"
	"cold-backend/internal/db"
	h "cold-backend/internal/http"
	"cold-backend/internal/handlers"
	"cold-backend/internal/middleware"
	"cold-backend/internal/repositories"
	"cold-backend/internal/services"
)

func main() {
	// Load configuration
	cfg := config.Load()

	// Connect to database
	pool := db.Connect(cfg)
	defer pool.Close()

	// Initialize JWT manager
	jwtManager := auth.NewJWTManager(cfg)

	// Initialize repository
	repo := repositories.NewUserRepository(pool)

	// Initialize service
	service := services.NewUserService(repo, jwtManager)

	// Initialize handlers
	userHandler := handlers.NewUserHandler(service)
	authHandler := handlers.NewAuthHandler(service)
	pageHandler := handlers.NewPageHandler()

	// Initialize middleware
	authMiddleware := middleware.NewAuthMiddleware(jwtManager)
	corsMiddleware := middleware.NewCORS(cfg)

	// Create router
	router := h.NewRouter(userHandler, authHandler, pageHandler, authMiddleware)

	// Wrap router with CORS
	handler := corsMiddleware(router)

	// Start server
	addr := fmt.Sprintf(":%d", cfg.Server.Port)
	log.Printf("Server running on %s", addr)
	if err := http.ListenAndServe(addr, handler); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
