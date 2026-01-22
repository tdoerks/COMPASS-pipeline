#!/bin/bash
#SBATCH --job-name=ecoli_2020_prophage_amr
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-2020-prophage-amr-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-2020-prophage-amr-%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "E. coli 2020 Prophage-AMR Analysis"
echo "Method 3 (Gold Standard) Only"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
RESULTS_DIR="/bulk/tylerdoe/archives/ecoli_2020_all_narms"
OUTPUT_DIR="/homes/tylerdoe/ecoli_2020_prophage_amr_analysis_$(date +%Y%m%d)"

# Create output directory
mkdir -p "$OUTPUT_DIR"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Check if directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo "❌ ERROR: Results directory not found: $RESULTS_DIR"
    exit 1
fi

echo "Results directory: $RESULTS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Count samples
SAMPLE_COUNT=$(find "$RESULTS_DIR/amrfinder" -name "*_amr.tsv" 2>/dev/null | wc -l)
PROPHAGE_COUNT=$(find "$RESULTS_DIR/vibrant" -name "*_phages.fna" 2>/dev/null | wc -l)

echo "Dataset: E. coli 2020"
echo "  Samples with AMR results: $SAMPLE_COUNT"
echo "  Samples with prophage data: $PROPHAGE_COUNT"
echo ""

# ============================================================================
# METHOD 3: Direct AMRFinder Scan (GOLD STANDARD)
# ============================================================================

echo "=========================================="
echo "METHOD 3: Direct AMRFinder Scan"
echo "=========================================="
echo "(This is the definitive method - extracts and scans prophage DNA)"
echo ""
START_TIME=$(date +%s)

./bin/run_amrfinder_on_prophages.py \
    "$RESULTS_DIR" \
    > "$OUTPUT_DIR/method3_direct_scan.log" 2>&1 <<EOF
y
EOF

METHOD3_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

# Move CSV output
if [ -f "$HOME/prophage_amr_direct_scan.csv" ]; then
    mv "$HOME/prophage_amr_direct_scan.csv" "$OUTPUT_DIR/method3_direct_scan.csv"
fi

if [ $METHOD3_EXIT -eq 0 ]; then
    echo "✅ Method 3 completed in ${HOURS}h ${MINUTES}m"
    if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
        GENES_IN_PROPHAGE=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
            awk -F',' '$2 != "None" && $2 != ""' | wc -l)
        echo "   Samples with AMR in prophages: $GENES_IN_PROPHAGE"
    fi
else
    echo "❌ Method 3 failed"
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "=========================================="
echo "🎉 E. coli 2020 Analysis Complete!"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""

if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
    AMR_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)
    echo "📊 Final Results (Method 3 - Gold Standard):"
    echo "   E. coli 2020: $AMR_COUNT AMR genes in prophages"
    echo ""
fi

echo "Next step:"
echo "  Run comprehensive analysis with 2020-2024 data"
echo "  sbatch run_comprehensive_amr_prophage_analysis_2020-2024.sh"
echo ""
echo "To view detailed results:"
echo "  ls -lh $OUTPUT_DIR"
echo "  cat $OUTPUT_DIR/method3_direct_scan.log"
echo ""
echo "=========================================="

exit 0
