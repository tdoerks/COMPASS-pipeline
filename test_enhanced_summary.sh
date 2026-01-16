#!/bin/bash
#
# Test Enhanced COMPASS_SUMMARY with visualizations on partial Kansas results
# Run this on Beocat to see the new multi-tab HTML report with prophage pie chart
#

echo "=========================================="
echo "Testing Enhanced COMPASS_SUMMARY Module"
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

echo "Running Enhanced COMPASS_SUMMARY with visualizations..."
echo ""

./bin/generate_compass_summary.py \
  --outdir $OUTDIR \
  --output_tsv ${OUTDIR}/summary/compass_summary.tsv \
  --output_html ${OUTDIR}/summary/compass_summary.html \
  --metadata $METADATA

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Enhanced summary generation succeeded!"
    echo ""
    echo "Output files:"
    ls -lh ${OUTDIR}/summary/compass_summary.tsv ${OUTDIR}/summary/compass_summary.html
    echo ""
    echo "📊 NEW FEATURES in HTML report:"
    echo "  • Multi-tab interface (Overview, Data Table, Prophage Functional Diversity)"
    echo "  • Interactive prophage functional diversity pie chart"
    echo "  • Enhanced summary statistics"
    echo ""
    echo "To view:"
    echo "  1. Download ${OUTDIR}/summary/compass_summary.html to your computer"
    echo "  2. Open in web browser to see interactive visualizations"
else
    echo "❌ Summary generation failed with exit code $EXIT_CODE"
    echo ""
    echo "Check error messages above for details"
fi
echo "=========================================="

exit $EXIT_CODE
