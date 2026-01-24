#!/bin/bash

# ============================================================================
# Clean Phylogenetic Tree - Remove Colons from Sequence IDs
# ============================================================================
#
# Phylogenetic trees in Newick format use colons (:) to separate node names
# from branch lengths. If sequence IDs contain colons (e.g., from VIBRANT
# output like "SRR123:NODE_5:cov_42.3:fragment_1"), tree viewers fail to
# parse the file.
#
# This script:
# 1. Extracts just the tree (removes FastTree log messages)
# 2. Replaces ALL colons with underscores
# 3. Restores colons only before branch lengths (numbers before delimiters)
#
# Usage:
#   bash clean_phylo_tree.sh input_tree.nwk output_tree_cleaned.nwk
#
# Or run without arguments to process the most recent tree:
#   bash clean_phylo_tree.sh
#
# ============================================================================

set -euo pipefail

# Function to show usage
usage() {
    echo "Usage: $0 [INPUT_TREE] [OUTPUT_TREE]"
    echo ""
    echo "Clean phylogenetic tree by removing colons from sequence IDs"
    echo ""
    echo "Arguments:"
    echo "  INPUT_TREE   Path to input Newick tree file (optional)"
    echo "  OUTPUT_TREE  Path to output cleaned tree file (optional)"
    echo ""
    echo "If no arguments provided, searches for most recent tree in:"
    echo "  - /homes/tylerdoe/*phylogeny*/amr_prophage_tree.nwk"
    echo "  - /homes/tylerdoe/*phylogeny*/prophage_tree.nwk"
    echo ""
    echo "Examples:"
    echo "  $0 tree.nwk tree_cleaned.nwk"
    echo "  $0  # Auto-find most recent tree"
    exit 1
}

# Check for help flag
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
fi

# Auto-detect tree file if not provided
if [ $# -eq 0 ]; then
    echo "No input file specified, searching for recent phylogeny trees..."
    echo ""

    # Search for trees
    TREE_FILES=$(find /homes/tylerdoe -maxdepth 2 -type f \
        \( -name "amr_prophage_tree.nwk" -o -name "prophage_tree.nwk" \) \
        2>/dev/null | sort -r)

    if [ -z "$TREE_FILES" ]; then
        echo "❌ ERROR: No phylogeny trees found"
        echo ""
        usage
    fi

    echo "Found phylogeny trees:"
    echo "$TREE_FILES" | nl
    echo ""

    # Use most recent
    INPUT_TREE=$(echo "$TREE_FILES" | head -1)
    echo "Using most recent: $INPUT_TREE"
    echo ""

    # Auto-generate output filename
    TREE_DIR=$(dirname "$INPUT_TREE")
    TREE_BASE=$(basename "$INPUT_TREE" .nwk)
    OUTPUT_TREE="${TREE_DIR}/${TREE_BASE}_cleaned.nwk"

elif [ $# -eq 1 ]; then
    INPUT_TREE="$1"
    # Auto-generate output filename
    TREE_DIR=$(dirname "$INPUT_TREE")
    TREE_BASE=$(basename "$INPUT_TREE" .nwk)
    OUTPUT_TREE="${TREE_DIR}/${TREE_BASE}_cleaned.nwk"

elif [ $# -eq 2 ]; then
    INPUT_TREE="$1"
    OUTPUT_TREE="$2"

else
    echo "❌ ERROR: Too many arguments"
    echo ""
    usage
fi

# Verify input file exists
if [ ! -f "$INPUT_TREE" ]; then
    echo "❌ ERROR: Input tree file not found: $INPUT_TREE"
    exit 1
fi

# Check input file size
INPUT_SIZE=$(stat -c%s "$INPUT_TREE" 2>/dev/null || stat -f%z "$INPUT_TREE")

if [ $INPUT_SIZE -lt 500 ]; then
    echo "⚠️  WARNING: Input file is very small (${INPUT_SIZE} bytes)"
    echo "   This may indicate an error file rather than a tree"
    echo ""
    echo "First 500 characters of input:"
    head -c 500 "$INPUT_TREE"
    echo ""
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
fi

echo "=========================================="
echo "Cleaning Phylogenetic Tree"
echo "=========================================="
echo ""
echo "Input:  $INPUT_TREE"
echo "Output: $OUTPUT_TREE"
echo ""

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

TREE_ONLY="$TEMP_DIR/tree_only.nwk"
TEMP_TREE="$TEMP_DIR/temp_tree.nwk"

# ============================================================================
# Step 1: Extract just the tree (remove FastTree log messages)
# ============================================================================

echo "Step 1: Extracting tree from file..."

# Tree should be the last line and start with parenthesis
tail -1 "$INPUT_TREE" > "$TREE_ONLY"

# Verify it looks like a tree
FIRST_CHAR=$(head -c 1 "$TREE_ONLY")
if [ "$FIRST_CHAR" != "(" ]; then
    echo "❌ ERROR: Tree doesn't start with '(' - may not be valid Newick format"
    echo "   First 200 characters:"
    head -c 200 "$TREE_ONLY"
    echo ""
    exit 1
fi

TREE_ONLY_SIZE=$(stat -c%s "$TREE_ONLY" 2>/dev/null || stat -f%z "$TREE_ONLY")
echo "   ✅ Extracted tree (${TREE_ONLY_SIZE} bytes)"
echo ""

# ============================================================================
# Step 2: Replace all colons with underscores
# ============================================================================

echo "Step 2: Replacing colons with underscores..."

sed 's/:/_/g' "$TREE_ONLY" > "$TEMP_TREE"

TEMP_SIZE=$(stat -c%s "$TEMP_TREE" 2>/dev/null || stat -f%z "$TEMP_TREE")
echo "   ✅ Replaced colons (${TEMP_SIZE} bytes)"
echo ""

# ============================================================================
# Step 3: Restore colons before branch lengths only
# ============================================================================

echo "Step 3: Restoring colons before branch lengths..."

# This regex matches: underscore + decimal number + delimiter (,);)
# Only these underscores get converted back to colons (branch lengths)
sed -E 's/_([0-9]+\.[0-9]+)([,);])/:\1\2/g' "$TEMP_TREE" > "$OUTPUT_TREE"

OUTPUT_SIZE=$(stat -c%s "$OUTPUT_TREE" 2>/dev/null || stat -f%z "$OUTPUT_TREE")
echo "   ✅ Restored branch length colons (${OUTPUT_SIZE} bytes)"
echo ""

# ============================================================================
# Verification
# ============================================================================

echo "=========================================="
echo "Verification"
echo "=========================================="
echo ""

# Check output file
if [ ! -f "$OUTPUT_TREE" ] || [ ! -s "$OUTPUT_TREE" ]; then
    echo "❌ ERROR: Output file was not created or is empty"
    exit 1
fi

echo "✅ Output file created: $OUTPUT_TREE"
echo "   Size: $((OUTPUT_SIZE / 1024)) KB"
echo ""

# Show first 300 characters
echo "First 300 characters of cleaned tree:"
head -c 300 "$OUTPUT_TREE"
echo ""
echo ""

# Count nodes (approximate)
NODE_COUNT=$(grep -o "(" "$OUTPUT_TREE" | wc -l)
echo "Approximate node count: $NODE_COUNT"
echo ""

echo "=========================================="
echo "✅ TREE CLEANING COMPLETE!"
echo "=========================================="
echo ""
echo "Cleaned tree: $OUTPUT_TREE"
echo ""
echo "Next steps:"
echo "1. Download to local machine:"
echo "   scp tylerdoe@beocat.ksu.edu:$OUTPUT_TREE ."
echo ""
echo "2. Upload to iTOL:"
echo "   https://itol.embl.de/"
echo ""
echo "3. Or view with FigTree:"
echo "   figtree $(basename "$OUTPUT_TREE")"
echo ""

exit 0
