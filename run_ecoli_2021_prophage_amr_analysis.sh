#!/bin/bash
#SBATCH --job-name=ecoli_2021_prophage_amr
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-2021-prophage-amr-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-2021-prophage-amr-%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "E. coli 2021 Prophage-AMR Analysis"
echo "All 3 Methods"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
RESULTS_DIR="/bulk/tylerdoe/archives/kansas_2021_ecoli"
OUTPUT_DIR="/homes/tylerdoe/ecoli_2021_prophage_amr_analysis_$(date +%Y%m%d)"

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

echo "Dataset: E. coli 2021"
echo "  Samples with AMR results: $SAMPLE_COUNT"
echo "  Samples with prophage data: $PROPHAGE_COUNT"
echo ""

# ============================================================================
# METHOD 1: Coordinate-Based Analysis
# ============================================================================

echo "=========================================="
echo "METHOD 1: Coordinate-Based Analysis"
echo "=========================================="
echo ""
START_TIME=$(date +%s)

./bin/analyze_true_amr_prophage_colocation.py \
    "$RESULTS_DIR" \
    "$OUTPUT_DIR/method1_coordinate_based.csv"

METHOD1_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

if [ $METHOD1_EXIT -eq 0 ]; then
    echo "✅ Method 1 completed in ${ELAPSED}s"
    if [ -f "$OUTPUT_DIR/method1_coordinate_based.csv" ]; then
        COLOCATION_COUNT=$(tail -n +2 "$OUTPUT_DIR/method1_coordinate_based.csv" | \
            awk -F',' '$NF == "within_prophage"' | wc -l)
        echo "   AMR genes in prophages: $COLOCATION_COUNT"
    fi
else
    echo "❌ Method 1 failed"
fi
echo ""

# ============================================================================
# METHOD 2: Annotation Search
# ============================================================================

echo "=========================================="
echo "METHOD 2: Annotation-Based Search"
echo "=========================================="
echo ""
START_TIME=$(date +%s)

./bin/search_amr_in_vibrant_annotations.py \
    "$RESULTS_DIR" \
    > "$OUTPUT_DIR/method2_annotation_search.log" 2>&1

METHOD2_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

# Move CSV output
if [ -f "$HOME/amr_in_vibrant_annotations.csv" ]; then
    mv "$HOME/amr_in_vibrant_annotations.csv" "$OUTPUT_DIR/method2_annotation_search.csv"
fi

if [ $METHOD2_EXIT -eq 0 ]; then
    echo "✅ Method 2 completed in ${ELAPSED}s"
    if [ -f "$OUTPUT_DIR/method2_annotation_search.csv" ]; then
        MATCH_COUNT=$(tail -n +2 "$OUTPUT_DIR/method2_annotation_search.csv" | wc -l)
        echo "   Matches found: $MATCH_COUNT"
    fi
else
    echo "❌ Method 2 failed"
fi
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
echo "🎉 E. coli 2021 Analysis Complete!"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "Results saved to: $OUTPUT_DIR"
echo ""

if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
    AMR_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
        awk -F',' '$2 != "None" && $2 != ""' | wc -l)
    echo "📊 Final Results (Method 3 - Gold Standard):"
    echo "   E. coli 2021: $AMR_COUNT AMR genes in prophages"
    echo ""
fi

echo "To view detailed results:"
echo "  ls -lh $OUTPUT_DIR"
echo "  cat $OUTPUT_DIR/method3_direct_scan.log"
echo ""
echo "=========================================="

exit 0
