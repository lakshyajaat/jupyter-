package http

import (
	"github.com/gorilla/mux"
	"cold-backend/internal/handlers"
)

func NewRouter(userHandler *handlers.UserHandler) *mux.Router {
	r := mux.NewRouter()

	r.HandleFunc("/users", userHandler.CreateUser).Methods("POST")
	r.HandleFunc("/users/{id}", userHandler.GetUser).Methods("GET")

	return r
}
