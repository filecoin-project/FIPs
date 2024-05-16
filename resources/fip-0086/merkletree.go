package merkletree

import (
	"math/bits"

	"golang.org/x/crypto/sha3"
)

// Digest is a 32-byte hash digest.
type Digest = [32]byte

// VerifyProof verifies that the given value maps to the given index in the
// merkle tree with the given root. It returns "more" if the value is not the
// last value in the merkle tree.
func VerifyProof(root Digest, index int, value []byte, proof []Digest) (valid bool, more bool) {
	digest := leafHash(value) // this is the "leaf" hash.

	// If the index is greater than 2^len(proof) - 1, it can't possibly be
	// part of this tree.
	if index > 1<<len(proof)-1 {
		return false, false
	}

	// Walk from the leaf to the root, hashing with each uncle.
	for i, uncle := range proof {
		// We read the bits of the index LSB to MSB. We're walking from the
		// _bottom_ of the tree to the top.
		if index&(1<<i) == 0 {
			// If we hit a left branch and the uncle (right-branch) is non-zero,
			// there are more values in the tree beyond the current index.
			more = more || uncle != (Digest{})
			digest = internalHash(digest, uncle)
		} else {
			digest = internalHash(uncle, digest)
		}
	}
	return root == digest, more
}

// MerkleRoot returns a the root of the merkle tree of the given values.
func MerkleRoot(values [][]byte) Digest {
	root, _ := MerkleRootWithProofs(values)
	return root
}

// MerkleRootWithProofs returns a the root of the merkle tree of the
// given values, along with merkle proofs for each leaf.
func MerkleRootWithProofs(values [][]byte) (Digest, [][]Digest) {
	return buildTree(bits.Len(uint(len(values))-1), values)
}

var internalMarker = []byte{0}
var leafMarker = []byte{1}

func internalHash(left Digest, right Digest) (out Digest) {
	hash := sha3.NewLegacyKeccak256()
	_, _ = hash.Write(internalMarker)
	_, _ = hash.Write(left[:])
	_, _ = hash.Write(right[:])
	copy(out[:], hash.Sum(out[:0]))
	return out
}

func leafHash(value []byte) (out Digest) {
	hash := sha3.NewLegacyKeccak256()
	_, _ = hash.Write(leafMarker)
	_, _ = hash.Write(value)
	copy(out[:], hash.Sum(out[:0]))
	return out
}

func appendPath(paths [][]Digest, element Digest) [][]Digest {
	for i := range paths {
		paths[i] = append(paths[i], element)
	}
	return paths
}

func buildTree(depth int, values [][]byte) (Digest, [][]Digest) {
	if len(values) == 0 {
		return Digest{}, nil
	} else if depth == 0 {
		if len(values) != 1 {
			panic("expected one value at the leaf")
		}
		return leafHash(values[0]), [][]Digest{nil}
	}

	split := min(1<<(depth-1), len(values))
	leftHash, leftPaths := buildTree(depth-1, values[:split])
	rightHash, rightPaths := buildTree(depth-1, values[split:])
	paths := append(appendPath(leftPaths, rightHash), appendPath(rightPaths, leftHash)...)

	return internalHash(leftHash, rightHash), paths
}
