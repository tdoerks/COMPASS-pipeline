#!/bin/bash

# Fix colons in phylogenetic tree node names
# Colons in sequence IDs conflict with Newick format (which uses : for branch lengths)

TREE_DIR="/homes/tylerdoe/kansas_2021-2025_amr_prophage_phylogeny_20260122"
TREE_FILE="${TREE_DIR}/amr_prophage_tree.nwk"
CLEANED_TREE="${TREE_DIR}/amr_prophage_tree_cleaned.nwk"
METADATA_FILE="${TREE_DIR}/amr_prophage_metadata.tsv"
CLEANED_METADATA="${TREE_DIR}/amr_prophage_metadata_cleaned.tsv"

echo "==========================================="
echo "Fixing Newick Tree Format Issues"
echo "==========================================="
echo ""

# Check if tree file exists
if [ ! -f "$TREE_FILE" ]; then
    echo "❌ ERROR: Tree file not found: $TREE_FILE"
    exit 1
fi

echo "Original tree file: $TREE_FILE"
echo "Cleaned tree file: $CLEANED_TREE"
echo ""

# Replace colons in sequence IDs with underscores
# This regex finds colons that are NOT followed by a number (branch lengths)
# and replaces them with underscores
sed -E 's/([A-Za-z0-9]+):([A-Za-z0-9_]+):/\1_\2_/g' "$TREE_FILE" > "$CLEANED_TREE"

# Verify the cleaned file was created
if [ -f "$CLEANED_TREE" ] && [ -s "$CLEANED_TREE" ]; then
    echo "✅ Created cleaned tree: $CLEANED_TREE"
    echo ""
    echo "First 500 characters of cleaned tree:"
    head -c 500 "$CLEANED_TREE"
    echo ""
    echo ""
else
    echo "❌ ERROR: Failed to create cleaned tree"
    exit 1
fi

# Also clean the metadata file to match
if [ -f "$METADATA_FILE" ]; then
    echo "Cleaning metadata file to match..."

    # Replace colons with underscores in the sequence_id column (first column)
    awk 'BEGIN {FS=OFS="\t"}
         NR==1 {print; next}  # Keep header unchanged
         {gsub(/:/, "_", $1); print}' \
         "$METADATA_FILE" > "$CLEANED_METADATA"

    if [ -f "$CLEANED_METADATA" ] && [ -s "$CLEANED_METADATA" ]; then
        echo "✅ Created cleaned metadata: $CLEANED_METADATA"
    else
        echo "⚠️  WARNING: Could not create cleaned metadata"
    fi
else
    echo "⚠️  No metadata file found to clean"
fi

echo ""
echo "==========================================="
echo "Download these cleaned files:"
echo "==========================================="
echo ""
echo "scp tylerdoe@beocat.ksu.edu:${CLEANED_TREE} ."
echo "scp tylerdoe@beocat.ksu.edu:${CLEANED_METADATA} ."
echo ""
echo "Then upload amr_prophage_tree_cleaned.nwk to iTOL"
echo ""
