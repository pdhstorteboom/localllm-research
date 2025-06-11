package main

import (
	"context"
	"log"
	"net/url"
	"os"
	"strings"
	"time"

	"collector-go/fetcher"
	"collector-go/models"
	"collector-go/storage"
)

func main() {
	urls := os.Args[1:]
	if len(urls) == 0 {
		log.Fatal("geef een of meer document-URL's als argument")
	}

	f := fetcher.NewFetcher(3, 30*time.Second)
	store, err := storage.NewRawStore("collector-go-data")
	if err != nil {
		log.Fatalf("kan opslag niet initialiseren: %v", err)
	}

	for _, target := range urls {
		target = strings.TrimSpace(target)
		if target == "" {
			continue
		}

		ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
		result, err := f.Fetch(ctx, target)
		cancel()
		if err != nil {
			log.Printf("download mislukt voor %s: %v", target, err)
			continue
		}

		meta := models.DocumentMetadata{
			Source:        detectSource(target),
			URL:           target,
			RetrievedAt:   time.Now().UTC(),
			DocumentType:  result.SuspectedDocumentType(),
			ContentLength: len(result.Body),
			StatusCode:    result.StatusCode,
		}

		savedMeta, err := store.Save(result.Body, meta)
		if err != nil {
			log.Printf("opslaan mislukt voor %s: %v", target, err)
			continue
		}
		log.Printf("opgeslagen %s (%s) -> %s", target, savedMeta.DocumentType, savedMeta.StoragePath)
	}
}

func detectSource(rawURL string) string {
	parsed, err := url.Parse(rawURL)
	if err != nil || parsed.Host == "" {
		return "unknown"
	}
	return parsed.Host
}
