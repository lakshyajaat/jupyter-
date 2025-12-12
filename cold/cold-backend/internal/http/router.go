package http

import (
	"net/http"
	"github.com/gorilla/mux"
	"cold-backend/internal/handlers"
	"cold-backend/internal/middleware"
)

func NewRouter(
	userHandler *handlers.UserHandler,
	authHandler *handlers.AuthHandler,
	pageHandler *handlers.PageHandler,
	authMiddleware *middleware.AuthMiddleware,
) *mux.Router {
	r := mux.NewRouter()

	// Serve static files
	r.PathPrefix("/static/").Handler(http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))

	// Public HTML pages
	r.HandleFunc("/", pageHandler.LoginPage).Methods("GET")
	r.HandleFunc("/login", pageHandler.LoginPage).Methods("GET")

	// API routes - Authentication
	r.HandleFunc("/auth/signup", authHandler.Signup).Methods("POST")
	r.HandleFunc("/auth/login", authHandler.Login).Methods("POST")

	// Logout route
	r.HandleFunc("/logout", pageHandler.LogoutPage).Methods("GET")

	// Protected HTML pages
	r.HandleFunc("/dashboard", pageHandler.DashboardPage).Methods("GET")
	r.HandleFunc("/admin/dashboard", pageHandler.AdminDashboardPage).Methods("GET")
	r.HandleFunc("/item-search", pageHandler.ItemSearchPage).Methods("GET")
	r.HandleFunc("/events", pageHandler.EventTracerPage).Methods("GET")
	r.HandleFunc("/entry-room", pageHandler.EntryRoomPage).Methods("GET")
	r.HandleFunc("/main-entry", pageHandler.MainEntryPage).Methods("GET")
	r.HandleFunc("/room-config-1", pageHandler.RoomConfig1Page).Methods("GET")
	r.HandleFunc("/room-form-2", pageHandler.RoomForm2Page).Methods("GET")
	r.HandleFunc("/loading-invoice", pageHandler.LoadingInvoicePage).Methods("GET")

	// Employee management page (admin only)
	r.HandleFunc("/employees", pageHandler.EmployeesPage).Methods("GET")

	// Protected API routes - Users
	protected := r.PathPrefix("/api/users").Subrouter()
	protected.Use(authMiddleware.Authenticate)
	protected.HandleFunc("", userHandler.ListUsers).Methods("GET")
	protected.HandleFunc("", userHandler.CreateUser).Methods("POST")
	protected.HandleFunc("/{id}", userHandler.GetUser).Methods("GET")
	protected.HandleFunc("/{id}", userHandler.UpdateUser).Methods("PUT")
	protected.HandleFunc("/{id}", userHandler.DeleteUser).Methods("DELETE")

	return r
}
