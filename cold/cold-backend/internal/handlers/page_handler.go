package handlers

import (
	"html/template"
	"net/http"
	"path/filepath"
)

type PageHandler struct {
	templates *template.Template
}

func NewPageHandler() *PageHandler {
	// Parse all templates
	templates := template.Must(template.ParseGlob(filepath.Join("templates", "*.html")))

	return &PageHandler{
		templates: templates,
	}
}

// LoginPage serves the login page
func (h *PageHandler) LoginPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "user_login.html", nil)
}

// DashboardPage serves the dashboard (check session/auth first)
func (h *PageHandler) DashboardPage(w http.ResponseWriter, r *http.Request) {
	// TODO: Check if user is authenticated via session or JWT
	h.templates.ExecuteTemplate(w, "dashboard_employee.html", nil)
}

// AdminDashboardPage serves admin dashboard
func (h *PageHandler) AdminDashboardPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "dashboard_admin.html", nil)
}

// ItemSearchPage serves item search page
func (h *PageHandler) ItemSearchPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "itam_serch.html", nil)
}

// EventTracerPage serves event tracer page
func (h *PageHandler) EventTracerPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "event_tracer.html", nil)
}

// EntryRoomPage serves entry room page
func (h *PageHandler) EntryRoomPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "entry_room.html", nil)
}

// MainEntryPage serves main entry page
func (h *PageHandler) MainEntryPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "main_entry.html", nil)
}

// RoomForm1Page serves room form 1
func (h *PageHandler) RoomForm1Page(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "room_form_1.html", nil)
}

// RoomForm2Page serves room form 2
func (h *PageHandler) RoomForm2Page(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "room_form_2.html", nil)
}

// LoadingInvoicePage serves loading invoice page
func (h *PageHandler) LoadingInvoicePage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "loding_invoice.html", nil)
}

// RoomConfig1Page serves room configuration 1
func (h *PageHandler) RoomConfig1Page(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "room-config-1.html", nil)
}

// LogoutPage handles logout
func (h *PageHandler) LogoutPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "logout.html", nil)
}

// EmployeesPage serves employee management page
func (h *PageHandler) EmployeesPage(w http.ResponseWriter, r *http.Request) {
	h.templates.ExecuteTemplate(w, "employees.html", nil)
}
