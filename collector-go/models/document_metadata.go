package models

import "time"

// DocumentMetadata houdt bij hoe en wanneer een document is opgehaald.
type DocumentMetadata struct {
	Source        string            `json:"source"`
	URL           string            `json:"url"`
	RetrievedAt   time.Time         `json:"retrieved_at"`
	ContentHash   string            `json:"content_hash"`
	DocumentType  string            `json:"document_type,omitempty"`
	ContentLength int               `json:"content_length"`
	StatusCode    int               `json:"status_code"`
	StoragePath   string            `json:"storage_path"`
	Attributes    map[string]string `json:"attributes,omitempty"`
}
