package storage

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"

	"collector-go/models"
)

// Decision is het resultaat van een versie-evaluatie.
type Decision string

const (
	DecisionNew        Decision = "new"
	DecisionNewVersion Decision = "new-version"
	DecisionDuplicate  Decision = "duplicate"
)

// VersionDecision beschrijft hoe een document moet worden opgeslagen.
type VersionDecision struct {
	Decision     Decision
	Version      int
	PreviousHash string
}

type versionEntry struct {
	LatestHash string `json:"latest_hash"`
	Version    int    `json:"version"`
}

// VersionTracker bewaart persistente informatie over versies per bron.
type VersionTracker struct {
	mu      sync.Mutex
	path    string
	entries map[string]versionEntry
}

// NewVersionTracker laadt of initialiseert versie-informatie in basePath.
func NewVersionTracker(basePath string) (*VersionTracker, error) {
	indexPath := filepath.Join(basePath, "version_index.json")
	entries := make(map[string]versionEntry)

	if payload, err := os.ReadFile(indexPath); err == nil {
		if err := json.Unmarshal(payload, &entries); err != nil {
			return nil, err
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}

	return &VersionTracker{
		path:    indexPath,
		entries: entries,
	}, nil
}

// Evaluate beslist of een document nieuw, een nieuwe versie of een duplicaat is.
func (v *VersionTracker) Evaluate(meta models.DocumentMetadata, contentHash string) (VersionDecision, error) {
	v.mu.Lock()
	defer v.mu.Unlock()

	key := versionKey(meta)
	entry, ok := v.entries[key]
	decision := VersionDecision{
		PreviousHash: entry.LatestHash,
	}

	switch {
	case !ok:
		decision.Decision = DecisionNew
		decision.Version = 1
		v.entries[key] = versionEntry{
			LatestHash: contentHash,
			Version:    1,
		}
		return decision, v.persist()
	case entry.LatestHash == contentHash:
		decision.Decision = DecisionDuplicate
		decision.Version = entry.Version
		return decision, nil
	default:
		entry.Version++
		entry.LatestHash = contentHash
		v.entries[key] = entry
		decision.Decision = DecisionNewVersion
		decision.Version = entry.Version
		return decision, v.persist()
	}
}

func (v *VersionTracker) persist() error {
	payload, err := json.MarshalIndent(v.entries, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(v.path, payload, 0o644)
}

func versionKey(meta models.DocumentMetadata) string {
	if meta.URL != "" {
		return meta.URL
	}
	return meta.Source
}
