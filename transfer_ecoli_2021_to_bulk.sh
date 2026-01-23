#!/bin/bash
# Transfer E. coli 2021 results from fastscratch to bulk storage

echo "=========================================="
echo "Transferring E. coli 2021 to Bulk Storage"
echo "=========================================="
echo "Start time: $(date)"
echo ""

SOURCE="/fastscratch/tylerdoe/kansas_2021_ecoli"
DEST="/bulk/tylerdoe/archives/kansas_2021_ecoli"

# Check source exists
if [ ! -d "$SOURCE" ]; then
    echo "❌ ERROR: Source directory not found: $SOURCE"
    exit 1
fi

# Show size
echo "Source directory: $SOURCE"
echo "Destination: $DEST"
echo ""
echo "Calculating size..."
du -sh "$SOURCE"
echo ""

# Create destination directory
mkdir -p "$DEST"

echo "Starting rsync transfer..."
echo "Options:"
echo "  -av    : Archive mode (preserves permissions, timestamps)"
echo "  --progress : Show progress"
echo "  --stats    : Show transfer statistics"
echo ""

# Run rsync with progress
rsync -av --progress --stats "$SOURCE/" "$DEST/"

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Transfer Complete"
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Transfer completed successfully!"
    echo ""
    echo "Destination: $DEST"
    echo ""
    echo "Verifying key directories..."
    for dir in amrfinder vibrant quast mlst summary; do
        if [ -d "$DEST/$dir" ]; then
            COUNT=$(ls "$DEST/$dir" 2>/dev/null | wc -l)
            echo "  ✓ $dir: $COUNT files"
        else
            echo "  ⚠ $dir: Not found"
        fi
    done
    echo ""
    echo "Final size:"
    du -sh "$DEST"
else
    echo "❌ Transfer failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
