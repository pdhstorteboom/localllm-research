package storage

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"collector-go/models"
)

// RawStore persists raw documents and metadata independently.
type RawStore struct {
	basePath     string
	rawDir       string
	metadataDir  string
	permissions  os.FileMode
	metadataPerm os.FileMode
}

// NewRawStore prepares the folders used for raw data and metadata.
func NewRawStore(basePath string) (*RawStore, error) {
	rawDir := filepath.Join(basePath, "raw")
	metaDir := filepath.Join(basePath, "metadata")

	if err := os.MkdirAll(rawDir, 0o755); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(metaDir, 0o755); err != nil {
		return nil, err
	}

	return &RawStore{
		basePath:     basePath,
		rawDir:       rawDir,
		metadataDir:  metaDir,
		permissions:  0o644,
		metadataPerm: 0o644,
	}, nil
}

// Save writes raw data and its metadata entry.
func (s *RawStore) Save(data []byte, meta models.DocumentMetadata) (models.DocumentMetadata, error) {
	if len(data) == 0 {
		return meta, errors.New("geen data om op te slaan")
	}
	if meta.ContentHash == "" {
		return meta, errors.New("content hash ontbreekt voor opslag")
	}

	meta.ContentLength = len(data)
	meta.RetrievedAt = meta.RetrievedAt.UTC()

	rawFile := s.rawPath(meta.ContentHash)
	if _, err := os.Stat(rawFile); errors.Is(err, os.ErrNotExist) {
		if err := os.WriteFile(rawFile, data, s.permissions); err != nil {
			return meta, err
		}
	}
	meta.StoragePath = rawFile

	if err := s.writeMetadata(meta); err != nil {
		return meta, err
	}
	return meta, nil
}

// RecordMetadata stores an additional metadata entry for existing raw data.
func (s *RawStore) RecordMetadata(meta models.DocumentMetadata) error {
	if meta.ContentHash == "" {
		return errors.New("content hash ontbreekt voor metadata")
	}
	meta.RetrievedAt = meta.RetrievedAt.UTC()
	if meta.StoragePath == "" {
		meta.StoragePath = s.rawPath(meta.ContentHash)
	}
	return s.writeMetadata(meta)
}

// RawPath returns the path under which a hash is stored.
func (s *RawStore) RawPath(hash string) string {
	return s.rawPath(hash)
}

func (s *RawStore) rawPath(hash string) string {
	return filepath.Join(s.rawDir, hash+".bin")
}

func (s *RawStore) writeMetadata(meta models.DocumentMetadata) error {
	metaFile := filepath.Join(
		s.metadataDir,
		fmt.Sprintf("%s-%d.json", meta.ContentHash, time.Now().UTC().UnixNano()),
	)
	payload, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(metaFile, payload, s.metadataPerm)
}
