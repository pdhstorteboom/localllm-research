package fetcher

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path/filepath"
	"strings"
	"time"
)

const maxDocumentSize = 25 * 1024 * 1024 // Upper bound for raw downloads.

// FetchResult bundles raw bytes and associated metadata.
type FetchResult struct {
	Body        []byte
	ContentType string
	StatusCode  int
	URL         string
}

// SuspectedDocumentType attempts to infer the document type from headers or extension.
func (r FetchResult) SuspectedDocumentType() string {
	ct := strings.ToLower(r.ContentType)
	switch {
	case strings.Contains(ct, "pdf"):
		return "pdf"
	case strings.Contains(ct, "html"), strings.Contains(ct, "htm"):
		return "html"
	case strings.Contains(ct, "plain"):
		return "text"
	}

	parsed, err := url.Parse(r.URL)
	if err != nil {
		return "unknown"
	}
	ext := strings.ToLower(filepath.Ext(parsed.Path))
	switch ext {
	case ".pdf":
		return "pdf"
	case ".html", ".htm":
		return "html"
	case ".txt":
		return "text"
	default:
		return "unknown"
	}
}

// Fetcher downloads documents with retry and timeout handling.
type Fetcher struct {
	client     *http.Client
	maxRetries int
	retryDelay time.Duration
}

// NewFetcher constructs a fetcher using the provided retry count and timeout.
func NewFetcher(maxRetries int, timeout time.Duration) *Fetcher {
	if maxRetries < 0 {
		maxRetries = 0
	}
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.ResponseHeaderTimeout = timeout

	return &Fetcher{
		client: &http.Client{
			Timeout:   timeout,
			Transport: transport,
		},
		maxRetries: maxRetries,
		retryDelay: 2 * time.Second,
	}
}

// Fetch downloads a document while honoring retryable failures.
func (f *Fetcher) Fetch(ctx context.Context, targetURL string) (*FetchResult, error) {
	var lastErr error
	for attempt := 0; attempt <= f.maxRetries; attempt++ {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
		}

		req, err := http.NewRequestWithContext(ctx, http.MethodGet, targetURL, nil)
		if err != nil {
			return nil, err
		}
		req.Header.Set("User-Agent", "PROCESSING-LLM-01-collector/0.1")

		resp, err := f.client.Do(req)
		if err != nil {
			if !errors.Is(err, context.DeadlineExceeded) && !errors.Is(err, context.Canceled) {
				lastErr = err
				time.Sleep(f.backoff(attempt))
				continue
			}
			return nil, err
		}

		body, readErr := io.ReadAll(io.LimitReader(resp.Body, maxDocumentSize))
		resp.Body.Close()
		if readErr != nil {
			lastErr = readErr
			time.Sleep(f.backoff(attempt))
			continue
		}

		if resp.StatusCode >= 500 || resp.StatusCode == http.StatusTooManyRequests {
			lastErr = fmt.Errorf("temporary status %d", resp.StatusCode)
			time.Sleep(f.backoff(attempt))
			continue
		}
		if resp.StatusCode >= 400 {
			return nil, fmt.Errorf("non-retryable status %d for %s", resp.StatusCode, targetURL)
		}

		return &FetchResult{
			Body:        body,
			ContentType: resp.Header.Get("Content-Type"),
			StatusCode:  resp.StatusCode,
			URL:         targetURL,
		}, nil
	}
	if lastErr == nil {
		lastErr = fmt.Errorf("exhausted retries for %s", targetURL)
	}
	return nil, lastErr
}

func (f *Fetcher) backoff(attempt int) time.Duration {
	delay := time.Duration(attempt+1) * f.retryDelay
	if delay > 15*time.Second {
		return 15 * time.Second
	}
	return delay
}
