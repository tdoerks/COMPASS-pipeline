#!/bin/bash
#
# Test COMPASS_SUMMARY module on partial Kansas results
# This runs the same summary that will execute at pipeline completion
#

echo "=========================================="
echo "Testing COMPASS_SUMMARY Module"
echo "=========================================="
echo ""

# Navigate to pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

OUTDIR="/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"

echo "Output directory: $OUTDIR"
echo ""

# Check if output directory exists
if [ ! -d "$OUTDIR" ]; then
    echo "ERROR: Output directory not found: $OUTDIR"
    exit 1
fi

# Check if metadata file exists
METADATA="${OUTDIR}/filtered_samples/filtered_samples.csv"
if [ ! -f "$METADATA" ]; then
    echo "ERROR: Metadata file not found: $METADATA"
    exit 1
fi

echo "Found metadata file: $METADATA"
echo "Sample count: $(tail -n +2 $METADATA | wc -l)"
echo ""

# Count completed results
echo "Checking completed results:"
mlst_count=$(ls ${OUTDIR}/mlst/*.tsv 2>/dev/null | wc -l)
amr_count=$(ls ${OUTDIR}/amrfinder/*_amr.tsv 2>/dev/null | wc -l)
mob_count=$(ls -d ${OUTDIR}/mobsuite/*_mobsuite 2>/dev/null | wc -l)

echo "  MLST results: $mlst_count"
echo "  AMRFinder results: $amr_count"
echo "  MOB-suite results: $mob_count"
echo ""

echo "Running COMPASS_SUMMARY..."
echo ""

./bin/generate_compass_summary.py \
  --outdir $OUTDIR \
  --output_tsv test_summary.tsv \
  --output_html test_summary.html \
  --metadata $METADATA

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Summary generation succeeded!"
    echo ""
    echo "Output files:"
    ls -lh test_summary.tsv test_summary.html
    echo ""
    echo "Preview summary (first 10 lines):"
    head -10 test_summary.tsv
    echo ""
    echo "To view full results:"
    echo "  cat test_summary.tsv"
    echo "  less test_summary.html"
else
    echo "❌ Summary generation failed with exit code $EXIT_CODE"
    echo ""
    echo "Check error messages above for details"
fi
echo "=========================================="

exit $EXIT_CODE
