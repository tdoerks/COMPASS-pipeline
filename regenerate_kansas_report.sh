#!/bin/bash

# Regenerate Kansas 2021-2025 COMPASS Summary Report
# with all new Phase 1-10, 12, 13 enhancements
#
# This script regenerates ONLY the HTML/TSV summary reports
# using existing pipeline results. No re-analysis is performed.
#
# Usage: bash regenerate_kansas_report.sh
# Or submit as SLURM job: sbatch regenerate_kansas_report.sh

#SBATCH --job-name=regen_ks_report
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

echo "=========================================="
echo "Regenerating COMPASS Summary Report"
echo "Kansas 2021-2025 NARMS Data"
echo "=========================================="
echo "Job ID: ${SLURM_JOB_ID:-interactive}"
echo "Start time: $(date)"
echo ""

# Directories
RESULTS_DIR="/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"
METADATA_FILE="$RESULTS_DIR/metadata/filtered_samples.csv"
OUTPUT_HTML="$RESULTS_DIR/summary/compass_summary_enhanced.html"
OUTPUT_TSV="$RESULTS_DIR/summary/compass_summary_enhanced.tsv"

echo "Results directory: $RESULTS_DIR"
echo "Metadata file: $METADATA_FILE"
echo "Output HTML: $OUTPUT_HTML"
echo "Output TSV: $OUTPUT_TSV"
echo ""

# Check if results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "ERROR: Results directory not found!"
    echo "Expected: $RESULTS_DIR"
    exit 1
fi

# Load Python module
module load Python/3.9

# Check if metadata file exists
if [ -f "$METADATA_FILE" ]; then
    echo "✓ Metadata file found"
    METADATA_ARG="--metadata $METADATA_FILE"
else
    echo "⚠ Metadata file not found - report will have limited info"
    METADATA_ARG=""
fi

echo ""
echo "=========================================="
echo "Running enhanced report generator..."
echo "=========================================="
echo ""
echo "New features in this report:"
echo "  ✓ Phase 1-8: Core visualizations (tabs, charts, tables)"
echo "  ✓ Phase 9: Geographic Analysis (state distributions, MDR by region)"
echo "  ✓ Phase 10: Strain Typing (MLST, serovars, strain diversity)"
echo "  ✓ Phase 12: Export features (JSON, PNG charts, PDF)"
echo "  ✓ Phase 13: Performance optimizations (pagination, decimation)"
echo ""
echo "Report will include:"
echo "  - 10 interactive tabs"
echo "  - 26+ visualizations"
echo "  - Downloadable exports (JSON, PNG, PDF)"
echo "  - Optimized for large datasets"
echo ""

# Change to pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Run the enhanced report generator
python3 bin/generate_compass_summary.py \
    --outdir "$RESULTS_DIR" \
    $METADATA_ARG \
    --output_html "$OUTPUT_HTML" \
    --output_tsv "$OUTPUT_TSV"

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Report generation complete!"
    echo ""
    echo "Enhanced HTML report:"
    echo "  $OUTPUT_HTML"
    echo ""
    echo "Enhanced TSV summary:"
    echo "  $OUTPUT_TSV"
    echo ""
    echo "New features available:"
    echo "  • Geographic Analysis tab - state-level MDR distributions"
    echo "  • Strain Typing tab - MLST and serovar visualizations"
    echo "  • Export toolbar - download JSON, PNG charts, or PDF report"
    echo "  • Table pagination - 50/100/500/All rows per page"
    echo ""
    echo "To view the report:"
    echo "  1. Copy to your local machine:"
    echo "     scp tylerdoe@beocat.cis.ksu.edu:$OUTPUT_HTML ."
    echo ""
    echo "  2. Open in your web browser"
    echo ""
    echo "Original report (for comparison):"
    echo "  $RESULTS_DIR/summary/compass_summary.html"
    echo ""
else
    echo ""
    echo "❌ Report generation failed!"
    echo ""
    echo "Check for errors above"
    echo "Log file: /homes/tylerdoe/slurm-${SLURM_JOB_ID}.out"
    echo ""
fi

exit $EXIT_CODE
