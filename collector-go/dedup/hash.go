package dedup

import (
	"crypto/sha256"
	"encoding/hex"
)

// ComputeHash returns a SHA-256 checksum for the provided bytes.
func ComputeHash(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}
