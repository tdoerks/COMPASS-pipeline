#!/bin/bash

# Copy preliminary E. coli 2024 results to analysis folder
# This preserves current progress while pipeline continues running

SOURCE="/fastscratch/tylerdoe/results_ecoli_all_2024"
DEST="/fastscratch/tylerdoe/results_ecoli_2024_preliminary"

echo "=========================================="
echo "Copying preliminary E. coli 2024 results"
echo "=========================================="
echo ""
echo "Source: $SOURCE"
echo "Destination: $DEST"
echo ""

# Check source exists
if [ ! -d "$SOURCE" ]; then
    echo "ERROR: Source directory not found!"
    exit 1
fi

# Create destination
mkdir -p "$DEST"

echo "Copying completed results..."
echo ""

# Copy key result directories (only if they exist and have content)
for dir in metadata filtered_samples mlst sistr amrfinder vibrant mobsuite diamond_prophage phanotate abricate quast species_validation; do
    if [ -d "$SOURCE/$dir" ] && [ "$(ls -A $SOURCE/$dir 2>/dev/null)" ]; then
        echo "  Copying $dir..."
        cp -r "$SOURCE/$dir" "$DEST/"
        count=$(find "$DEST/$dir" -type f | wc -l)
        echo "    → $count files copied"
    else
        echo "  Skipping $dir (empty or doesn't exist)"
    fi
done

echo ""
echo "=========================================="
echo "Summary of copied data:"
echo "=========================================="

# Count samples in each directory
for dir in mlst amrfinder vibrant mobsuite; do
    if [ -d "$DEST/$dir" ]; then
        count=$(find "$DEST/$dir" -name "*.tsv" -o -name "*.fasta" -o -name "*.fna" 2>/dev/null | wc -l)
        echo "  $dir: $count files"
    fi
done

echo ""
echo "✅ Copy complete!"
echo ""
echo "Location: $DEST"
echo ""
echo "Next steps:"
echo "  1. Run analysis scripts on preliminary data"
echo "  2. Pipeline continues running in background"
echo "  3. Re-run analyses on final complete dataset later"
