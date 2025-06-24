package main

import (
	"context"
	"log"
	"net/url"
	"os"
	"strings"
	"time"

	"collector-go/dedup"
	"collector-go/fetcher"
	"collector-go/models"
	"collector-go/storage"
)

func main() {
	urls := os.Args[1:]
	if len(urls) == 0 {
		log.Fatal("geef een of meer document-URL's als argument")
	}

	const basePath = "collector-go-data"

	f := fetcher.NewFetcher(3, 30*time.Second)
	store, err := storage.NewRawStore(basePath)
	if err != nil {
		log.Fatalf("kan opslag niet initialiseren: %v", err)
	}
	versionTracker, err := storage.NewVersionTracker(basePath)
	if err != nil {
		log.Fatalf("kan versie-tracker niet initialiseren: %v", err)
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

		hash := dedup.ComputeHash(result.Body)
		decision, err := versionTracker.Evaluate(meta, hash)
		if err != nil {
			log.Printf("versiebepaling mislukt voor %s: %v", target, err)
			continue
		}

		meta.ContentHash = hash
		meta.DedupDecision = string(decision.Decision)
		meta.Version = decision.Version
		meta.PreviousHash = decision.PreviousHash

		if decision.Decision == storage.DecisionDuplicate {
			meta.StoragePath = store.RawPath(hash)
			if err := store.RecordMetadata(meta); err != nil {
				log.Printf("metadata-registratie mislukt voor duplicaat %s: %v", target, err)
			} else {
				log.Printf("overgeslagen duplicaat %s (versie %d, hash %s)", target, decision.Version, hash)
			}
			continue
		}

		savedMeta, err := store.Save(result.Body, meta)
		if err != nil {
			log.Printf("opslaan mislukt voor %s: %v", target, err)
			continue
		}
		log.Printf("opgeslagen %s (%s) versie %d -> %s", target, savedMeta.DocumentType, savedMeta.Version, savedMeta.StoragePath)
	}
}

func detectSource(rawURL string) string {
	parsed, err := url.Parse(rawURL)
	if err != nil || parsed.Host == "" {
		return "unknown"
	}
	return parsed.Host
}
