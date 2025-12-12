package services

import (
	"context"
	"errors"

	"cold-backend/internal/models"
	"cold-backend/internal/repositories"
)

type EntryService struct {
	EntryRepo    *repositories.EntryRepository
	CustomerRepo *repositories.CustomerRepository
}

func NewEntryService(entryRepo *repositories.EntryRepository, customerRepo *repositories.CustomerRepository) *EntryService {
	return &EntryService{
		EntryRepo:    entryRepo,
		CustomerRepo: customerRepo,
	}
}

func (s *EntryService) CreateEntry(ctx context.Context, req *models.CreateEntryRequest, userID int) (*models.Entry, error) {
	// Validate quantity (1-1500 kg)
	if req.ExpectedQuantity < 1 || req.ExpectedQuantity > 1500 {
		return nil, errors.New("expected quantity must be between 1 and 1500 kg")
	}

	// Determine truck category based on quantity
	var category string
	if req.ExpectedQuantity >= 1 && req.ExpectedQuantity <= 600 {
		category = "seed"
	} else if req.ExpectedQuantity > 600 && req.ExpectedQuantity <= 1500 {
		category = "sell"
	} else {
		return nil, errors.New("invalid quantity range")
	}

	// Verify customer exists
	customer, err := s.CustomerRepo.Get(ctx, req.CustomerID)
	if err != nil {
		return nil, errors.New("customer not found")
	}

	// Create entry with denormalized customer data for historical record
	entry := &models.Entry{
		CustomerID:       customer.ID,
		Phone:            customer.Phone,
		Name:             customer.Name,
		Village:          customer.Village,
		ExpectedQuantity: req.ExpectedQuantity,
		TruckCategory:    category,
		CreatedByUserID:  userID,
	}

	if err := s.EntryRepo.Create(ctx, entry); err != nil {
		return nil, err
	}

	return entry, nil
}

func (s *EntryService) GetEntry(ctx context.Context, id int) (*models.Entry, error) {
	return s.EntryRepo.Get(ctx, id)
}

func (s *EntryService) ListEntries(ctx context.Context) ([]*models.Entry, error) {
	return s.EntryRepo.List(ctx)
}

func (s *EntryService) ListEntriesByCustomer(ctx context.Context, customerID int) ([]*models.Entry, error) {
	return s.EntryRepo.ListByCustomer(ctx, customerID)
}
