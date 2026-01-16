#!/bin/bash
# Regenerate COMPASS summary report (same as pipeline does)
# This recreates filtered metadata and generates the HTML report

set -e  # Exit on error

if [ $# -lt 1 ]; then
    echo "Usage: $0 <results_directory> [output_html]"
    echo ""
    echo "Example:"
    echo "  $0 /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"
    echo ""
    exit 1
fi

RESULTS_DIR="$1"
OUTPUT_HTML="${2:-compass_summary.html}"
OUTPUT_TSV="${OUTPUT_HTML%.html}.tsv"

echo "=========================================="
echo "COMPASS Report Regeneration"
echo "=========================================="
echo "Results directory: $RESULTS_DIR"
echo "Output HTML: $OUTPUT_HTML"
echo "Output TSV: $OUTPUT_TSV"
echo ""

# Step 1: Determine metadata source
METADATA_ARG=""

# Check if there's an existing summary TSV from the pipeline (has all metadata already)
if [ -f "$RESULTS_DIR/summary/compass_summary.tsv" ]; then
    echo "✓ Found existing summary TSV with metadata"
    METADATA_ARG="--metadata $RESULTS_DIR/summary/compass_summary.tsv"
# Otherwise try to recreate from metadata directory
elif [ -d "$RESULTS_DIR/metadata" ]; then
    echo "Step 1: Recreating filtered metadata from metadata directory..."
    echo ""
    ./bin/recreate_filtered_metadata.py --outdir "$RESULTS_DIR" || {
        echo "⚠️  WARNING: Metadata recreation failed, continuing anyway..."
    }
    echo ""

    if [ -f "$RESULTS_DIR/filtered_samples/filtered_samples.csv" ]; then
        METADATA_ARG="--metadata $RESULTS_DIR/filtered_samples/filtered_samples.csv"
    fi
else
    echo "⚠️  No metadata source found (no summary TSV or metadata directory)"
    echo "   Report will only have fields from result files (bases, spots, organism)"
fi

# Step 2: Generate comprehensive HTML report
echo "Step 2: Generating COMPASS summary report..."
echo ""
./bin/generate_compass_summary.py \
    --outdir "$RESULTS_DIR" \
    $METADATA_ARG \
    --output_html "$OUTPUT_HTML" \
    --output_tsv "$OUTPUT_TSV"

echo ""
echo "=========================================="
echo "✅ Report generation complete!"
echo "=========================================="
echo ""
echo "Output files:"
echo "  HTML: $OUTPUT_HTML"
echo "  TSV:  $OUTPUT_TSV"
echo "  Metadata: $RESULTS_DIR/filtered_samples/filtered_samples.csv"
echo ""
