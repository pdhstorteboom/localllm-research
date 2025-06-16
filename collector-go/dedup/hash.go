package dedup

import (
	"crypto/sha256"
	"encoding/hex"
)

// ComputeHash berekent een SHA-256 checksum voor de aangeleverde bytes.
func ComputeHash(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}
