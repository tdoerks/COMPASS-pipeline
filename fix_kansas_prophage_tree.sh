#!/bin/bash

TREE_DIR="/homes/tylerdoe/kansas_2021-2025_all_prophage_phylogeny_20260126"
TREE_FILE="${TREE_DIR}/prophage_tree.nwk"
CLEANED_TREE="${TREE_DIR}/prophage_tree_cleaned.nwk"
METADATA_FILE="${TREE_DIR}/prophage_metadata.tsv"
CLEANED_METADATA="${TREE_DIR}/prophage_metadata_cleaned.tsv"

echo "==========================================="
echo "Fixing Newick Tree Format (Colons)"
echo "==========================================="
echo ""

# Extract just the tree line (last line)
tail -1 "$TREE_FILE" > "$TREE_DIR/tree_only.nwk"

# Replace all colons with underscores
sed 's/:/_/g' "$TREE_DIR/tree_only.nwk" > "$TREE_DIR/temp_tree.nwk"

# Restore colons only before branch lengths (numbers)
sed -E 's/_([0-9]+\.[0-9]+)([,);])/:\1\2/g' "$TREE_DIR/temp_tree.nwk" > "$CLEANED_TREE"

# Clean up
rm -f "$TREE_DIR/tree_only.nwk" "$TREE_DIR/temp_tree.nwk"

if [ -f "$CLEANED_TREE" ] && [ -s "$CLEANED_TREE" ]; then
    echo "✅ Created: $CLEANED_TREE"
    echo ""
    echo "First 300 characters:"
    head -c 300 "$CLEANED_TREE"
    echo ""
else
    echo "❌ Failed to create cleaned tree"
    exit 1
fi

# Clean metadata
if [ -f "$METADATA_FILE" ]; then
    awk 'BEGIN {FS=OFS="\t"}
         NR==1 {print; next}
         {gsub(/:/, "_", $1); print}' \
         "$METADATA_FILE" > "$CLEANED_METADATA"
    echo "✅ Created: $CLEANED_METADATA"
fi

echo ""
echo "Download:"
echo "scp tylerdoe@beocat.ksu.edu:${CLEANED_TREE} ."
echo "scp tylerdoe@beocat.ksu.edu:${CLEANED_METADATA} ."
