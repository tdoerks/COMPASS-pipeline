#!/bin/bash
#SBATCH --job-name=kansas_2021-2025_prophage_amr
#SBATCH --output=/homes/tylerdoe/slurm-kansas-2021-2025-prophage-amr-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-kansas-2021-2025-prophage-amr-%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Kansas 2021-2025 Prophage-AMR Analysis"
echo "All 3 NARMS Organisms (Campy, Salmonella, E. coli)"
echo "Method 3 (Gold Standard)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
RESULTS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"
OUTPUT_DIR="/homes/tylerdoe/kansas_2021-2025_prophage_amr_analysis_$(date +%Y%m%d)"

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

echo "Dataset: Kansas 2021-2025 (All NARMS Organisms)"
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
echo "This will scan prophages from:"
echo "  - Campylobacter samples"
echo "  - Salmonella samples"
echo "  - E. coli samples"
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
        echo "   Total AMR genes in prophages: $GENES_IN_PROPHAGE"
        echo ""
        echo "   Breakdown by organism:"

        # Try to count by organism if organism info is in the metadata
        # This is approximate - relies on sample naming conventions
        CAMPY_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
            awk -F',' '$2 != "None" && $2 != "" && $1 ~ /[Cc]amp/' | wc -l)
        SAL_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
            awk -F',' '$2 != "None" && $2 != "" && $1 ~ /[Ss]al/' | wc -l)
        ECOLI_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
            awk -F',' '$2 != "None" && $2 != "" && $1 ~ /[Ee].*coli/' | wc -l)

        if [ $CAMPY_COUNT -gt 0 ] || [ $SAL_COUNT -gt 0 ] || [ $ECOLI_COUNT -gt 0 ]; then
            echo "     Campylobacter: $CAMPY_COUNT (approximate)"
            echo "     Salmonella: $SAL_COUNT (approximate)"
            echo "     E. coli: $ECOLI_COUNT (approximate)"
        fi
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
echo "🎉 Kansas 2021-2025 Prophage-AMR Analysis Complete!"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""

if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
    AMR_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)
    echo "📊 Final Results (Method 3 - Gold Standard):"
    echo "   Kansas 2021-2025: $AMR_COUNT AMR genes in prophages"
    echo ""
    echo "   This includes all three NARMS organisms:"
    echo "   - Campylobacter (chicken isolates)"
    echo "   - Salmonella (clinical & food)"
    echo "   - E. coli (clinical & food)"
    echo ""
fi

echo "Next steps:"
echo "  1. Run phylogeny on all prophages:"
echo "     sbatch run_kansas_2021-2025_all_prophage_phylogeny.sh"
echo ""
echo "  2. Run phylogeny on AMR-carrying prophages only:"
echo "     sbatch run_kansas_2021-2025_amr_prophage_phylogeny.sh"
echo ""
echo "To view detailed results:"
echo "  ls -lh $OUTPUT_DIR"
echo "  cat $OUTPUT_DIR/method3_direct_scan.log | tail -100"
echo ""
echo "=========================================="

exit 0
