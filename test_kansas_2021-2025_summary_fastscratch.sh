#!/bin/bash
# Test COMPASS summary generation on Kansas 2021-2025 data
# Using shared fastscratch location
# This tests the fixed HTML generation with working tabs and footer

echo "=========================================="
echo "Testing COMPASS Summary on Kansas 2021-2025"
echo "Location: /fastscratch/edwardbird_tylerdoe"
echo "=========================================="
echo ""

OUTDIR="/fastscratch/edwardbird_tylerdoe/kansas_2021-2025_all_narms_v1.2mod"
METADATA="${OUTDIR}/filtered_samples/filtered_samples.csv"

echo "Output directory: $OUTDIR"
echo "Metadata file: $METADATA"
echo ""

# Check if directory exists
if [ ! -d "$OUTDIR" ]; then
    echo "ERROR: Output directory not found: $OUTDIR"
    echo ""
    echo "Please run the copy script first:"
    echo "  ./copy_kansas_to_fastscratch.sh"
    exit 1
fi

# Check if metadata file exists
if [ ! -f "$METADATA" ]; then
    echo "ERROR: Metadata file not found: $METADATA"
    exit 1
fi

echo "Generating COMPASS summary with fixed HTML..."
echo ""

./bin/generate_compass_summary.py \
  --outdir $OUTDIR \
  --output_tsv ${OUTDIR}/compass_summary_FIXED.tsv \
  --output_html ${OUTDIR}/compass_summary_FIXED.html \
  --metadata $METADATA

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Summary generation succeeded!"
    echo ""
    echo "Output files:"
    ls -lh ${OUTDIR}/compass_summary_FIXED.tsv ${OUTDIR}/compass_summary_FIXED.html
    echo ""
    echo "📊 FIXED FEATURES in HTML report:"
    echo "  • Working tab switching (JavaScript properly closed)"
    echo "  • Footer shows actual Python/pandas versions (not literal {expressions})"
    echo "  • Geographic/MLST/Serovar data properly loaded (no {json.dumps(...)} literals)"
    echo "  • All interactive visualizations functional"
    echo ""
    echo "To view:"
    echo "  Download ${OUTDIR}/compass_summary_FIXED.html"
    echo "  Open in web browser and test tabs!"
else
    echo "❌ Summary generation failed with exit code $EXIT_CODE"
    echo ""
    echo "Check error messages above for details"
fi
echo "=========================================="

exit $EXIT_CODE
