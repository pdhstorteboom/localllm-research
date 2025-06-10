package storage

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"collector-go/models"
)

// RawStore bewaart ruwe documenten en metadata gescheiden.
type RawStore struct {
	basePath     string
	rawDir       string
	metadataDir  string
	permissions  os.FileMode
	metadataPerm os.FileMode
}

// NewRawStore initialiseert opslagmappen voor raw en metadata.
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

// Save slaat het ruwe document en een metadatarecord op.
func (s *RawStore) Save(data []byte, meta models.DocumentMetadata) (models.DocumentMetadata, error) {
	if len(data) == 0 {
		return meta, errors.New("geen data om op te slaan")
	}

	hash := sha256.Sum256(data)
	meta.ContentHash = hex.EncodeToString(hash[:])
	meta.ContentLength = len(data)
	meta.RetrievedAt = meta.RetrievedAt.UTC()

	rawFile := filepath.Join(s.rawDir, meta.ContentHash+".bin")
	if _, err := os.Stat(rawFile); errors.Is(err, os.ErrNotExist) {
		if err := os.WriteFile(rawFile, data, s.permissions); err != nil {
			return meta, err
		}
	}
	meta.StoragePath = rawFile

	metaFile := filepath.Join(
		s.metadataDir,
		fmt.Sprintf("%s-%d.json", meta.ContentHash, time.Now().UTC().UnixNano()),
	)
	payload, err := json.MarshalIndent(meta, "", "  ")
	if err != nil {
		return meta, err
	}
	if err := os.WriteFile(metaFile, payload, s.metadataPerm); err != nil {
		return meta, err
	}
	return meta, nil
}
