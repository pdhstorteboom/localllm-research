package models

import "time"

// DocumentMetadata tracks when and how a document was collected.
type DocumentMetadata struct {
	Source         string            `json:"source"`
	URL            string            `json:"url"`
	RetrievedAt    time.Time         `json:"retrieved_at"`
	ContentHash    string            `json:"content_hash"`
	DocumentType   string            `json:"document_type,omitempty"`
	ContentLength  int               `json:"content_length"`
	StatusCode     int               `json:"status_code"`
	StoragePath    string            `json:"storage_path"`
	DedupDecision  string            `json:"dedup_decision"`
	Version        int               `json:"version"`
	PreviousHash   string            `json:"previous_hash,omitempty"`
	AdditionalInfo map[string]string `json:"additional_info,omitempty"`
}
