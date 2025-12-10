package repositories

import (
	"context"
	"cold-backend/internal/models"
	"github.com/jackc/pgx/v5/pgxpool"
)

type UserRepository struct {
	DB *pgxpool.Pool
}

func NewUserRepository(db *pgxpool.Pool) *UserRepository {
	return &UserRepository{DB: db}
}

func (r *UserRepository) Create(ctx context.Context, u *models.User) error {
	_, err := r.DB.Exec(ctx,
		"INSERT INTO users(name, email) VALUES($1, $2)",
		u.Name, u.Email,
	)
	return err
}

func (r *UserRepository) Get(ctx context.Context, id int) (*models.User, error) {
	row := r.DB.QueryRow(ctx,
		"SELECT id, name, email FROM users WHERE id=$1", id)

	var user models.User
	err := row.Scan(&user.ID, &user.Name, &user.Email)
	return &user, err
}
