package repositories

import (
	"context"
	"fmt"
	"strings"

	"cold-backend/internal/models"
	"github.com/jackc/pgx/v5/pgxpool"
)

type EntryRepository struct {
	DB *pgxpool.Pool
}

func NewEntryRepository(db *pgxpool.Pool) *EntryRepository {
	return &EntryRepository{DB: db}
}

func (r *EntryRepository) Create(ctx context.Context, e *models.Entry) error {
	// Generate truck number based on category and entry count
	var count int
	err := r.DB.QueryRow(ctx, `SELECT COUNT(*) FROM entries WHERE truck_category = $1`, e.TruckCategory).Scan(&count)
	if err != nil {
		return err
	}

	// Generate truck number: SEED-001/450, SELL-001/800, etc.
	categoryUpper := strings.ToUpper(e.TruckCategory)
	truckNumber := fmt.Sprintf("%s-%03d/%d", categoryUpper, count+1, e.ExpectedQuantity)
	e.TruckNumber = truckNumber

	return r.DB.QueryRow(ctx,
		`INSERT INTO entries(customer_id, phone, name, village, expected_quantity, truck_category, truck_number, created_by_user_id)
         VALUES($1, $2, $3, $4, $5, $6, $7, $8)
         RETURNING id, created_at, updated_at`,
		e.CustomerID, e.Phone, e.Name, e.Village, e.ExpectedQuantity, e.TruckCategory, e.TruckNumber, e.CreatedByUserID,
	).Scan(&e.ID, &e.CreatedAt, &e.UpdatedAt)
}

func (r *EntryRepository) Get(ctx context.Context, id int) (*models.Entry, error) {
	row := r.DB.QueryRow(ctx,
		`SELECT id, customer_id, phone, name, village, expected_quantity, truck_category, truck_number, created_by_user_id, created_at, updated_at
         FROM entries WHERE id=$1`, id)

	var entry models.Entry
	err := row.Scan(&entry.ID, &entry.CustomerID, &entry.Phone, &entry.Name, &entry.Village,
		&entry.ExpectedQuantity, &entry.TruckCategory, &entry.TruckNumber, &entry.CreatedByUserID,
		&entry.CreatedAt, &entry.UpdatedAt)
	return &entry, err
}

func (r *EntryRepository) List(ctx context.Context) ([]*models.Entry, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT id, customer_id, phone, name, village, expected_quantity, truck_category, truck_number, created_by_user_id, created_at, updated_at
         FROM entries ORDER BY created_at DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []*models.Entry
	for rows.Next() {
		var entry models.Entry
		err := rows.Scan(&entry.ID, &entry.CustomerID, &entry.Phone, &entry.Name, &entry.Village,
			&entry.ExpectedQuantity, &entry.TruckCategory, &entry.TruckNumber, &entry.CreatedByUserID,
			&entry.CreatedAt, &entry.UpdatedAt)
		if err != nil {
			return nil, err
		}
		entries = append(entries, &entry)
	}
	return entries, nil
}

func (r *EntryRepository) ListByCustomer(ctx context.Context, customerID int) ([]*models.Entry, error) {
	rows, err := r.DB.Query(ctx,
		`SELECT id, customer_id, phone, name, village, expected_quantity, truck_category, truck_number, created_by_user_id, created_at, updated_at
         FROM entries WHERE customer_id=$1 ORDER BY created_at DESC`, customerID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var entries []*models.Entry
	for rows.Next() {
		var entry models.Entry
		err := rows.Scan(&entry.ID, &entry.CustomerID, &entry.Phone, &entry.Name, &entry.Village,
			&entry.ExpectedQuantity, &entry.TruckCategory, &entry.TruckNumber, &entry.CreatedByUserID,
			&entry.CreatedAt, &entry.UpdatedAt)
		if err != nil {
			return nil, err
		}
		entries = append(entries, &entry)
	}
	return entries, nil
}
