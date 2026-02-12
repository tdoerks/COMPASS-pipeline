#!/bin/bash
#
# Simple ETEC validation comparison script
# Run this after COMPASS pipeline completes
#

set -e

echo "========================================="
echo "ETEC Validation Comparison (Simplified)"
echo "========================================="
echo ""

# Check if results directory exists
RESULTS_DIR="data/validation/etec_results"
if [ ! -d "$RESULTS_DIR" ]; then
    echo "ERROR: Results directory not found: $RESULTS_DIR"
    echo ""
    echo "Expected structure:"
    echo "  $RESULTS_DIR/amrfinder/"
    echo "  $RESULTS_DIR/vibrant/"
    echo ""
    echo "Have you run the COMPASS pipeline yet?"
    echo "If results are on Beocat, run this script there or transfer results first."
    exit 1
fi

# Check for AMRFinder results
AMR_COUNT=$(ls $RESULTS_DIR/amrfinder/*_amr.tsv 2>/dev/null | wc -l)
if [ "$AMR_COUNT" -eq 0 ]; then
    echo "ERROR: No AMRFinder results found in $RESULTS_DIR/amrfinder/"
    exit 1
fi

echo "✓ Found $AMR_COUNT AMRFinder result files"
echo ""

# Output directory
OUTPUT_DIR="figures/etec_validation"
mkdir -p "$OUTPUT_DIR"

echo "✓ Output directory: $OUTPUT_DIR"
echo ""

# Check for Python script
SCRIPT="bin/compare_etec_validation_simple.py"
if [ ! -f "$SCRIPT" ]; then
    echo "ERROR: Validation script not found: $SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$SCRIPT"

# Generate figures
echo "Generating comparison figures..."
echo ""

python3 "$SCRIPT" "$RESULTS_DIR" --output "$OUTPUT_DIR"

echo ""
echo "========================================="
echo "✓ Comparison complete!"
echo "========================================="
echo ""
echo "Output location: $OUTPUT_DIR/"
echo ""
echo "Generated files:"
ls -lh "$OUTPUT_DIR/"
echo ""
echo "Next steps:"
echo "  1. Review amr_gene_comparison.csv for gene-by-gene comparison"
echo "  2. Check figure_s12_style_heatmap.png vs. paper Figure S12"
echo "  3. Review prophage_count_comparison.png vs. paper Table S4"
echo "  4. Check validation_summary_statistics.csv for overall metrics"
echo ""
