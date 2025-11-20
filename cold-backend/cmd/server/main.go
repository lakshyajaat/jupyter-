package main

import (
	"log"
	"net/http"

	"cold-backend/internal/config"
	"cold-backend/internal/db"
	h "cold-backend/internal/http"
	"cold-backend/internal/handlers"
	"cold-backend/internal/repositories"
	"cold-backend/internal/services"
)

func main() {
	cfg := config.Load()
	pool := db.Connect(cfg)

	repo := repositories.NewUserRepository(pool)
	service := services.NewUserService(repo)
	handler := handlers.NewUserHandler(service)

	router := h.NewRouter(handler)

	log.Printf("Server running on :%d", cfg.Server.Port)
	http.ListenAndServe(":8080", router)
}
