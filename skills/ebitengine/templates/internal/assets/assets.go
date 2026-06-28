package assets

import (
	"embed"
	"fmt"
)

//go:embed data/*
var files embed.FS

type Store struct {
	FS embed.FS
}

func Load() (*Store, error) {
	store := &Store{FS: files}
	if err := store.validate(); err != nil {
		return nil, err
	}
	return store, nil
}

func (s *Store) validate() error {
	entries, err := s.FS.ReadDir("data")
	if err != nil {
		return fmt.Errorf("read embedded data: %w", err)
	}
	if len(entries) == 0 {
		return fmt.Errorf("embedded data directory is empty")
	}
	return nil
}
