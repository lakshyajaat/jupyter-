package services

import (
	"context"
	"cold-backend/internal/models"
	"cold-backend/internal/repositories"
)

type UserService struct {
	Repo *repositories.UserRepository
}

func NewUserService(repo *repositories.UserRepository) *UserService {
	return &UserService{Repo: repo}
}

func (s *UserService) CreateUser(ctx context.Context, u *models.User) error {
	return s.Repo.Create(ctx, u)
}

func (s *UserService) GetUser(ctx context.Context, id int) (*models.User, error) {
	return s.Repo.Get(ctx, id)
}
