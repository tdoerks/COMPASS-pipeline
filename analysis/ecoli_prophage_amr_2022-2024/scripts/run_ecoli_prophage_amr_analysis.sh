#!/bin/bash
#SBATCH --job-name=ecoli_prophage_amr
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-prophage-amr-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-prophage-amr-%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "E. coli Prophage-AMR Analysis"
echo "All 3 Methods on Multiple E. coli Datasets"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_BASE="/homes/tylerdoe/ecoli_prophage_amr_analysis_$(date +%Y%m%d)"

# Create base output directory
mkdir -p "$OUTPUT_BASE"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Define datasets to analyze
declare -A DATASETS=(
    ["ecoli_2022"]="/bulk/tylerdoe/archives/kansas_2022_ecoli"
    ["ecoli_2023"]="/bulk/tylerdoe/archives/results_ecoli_2023"
    ["ecoli_2024"]="/bulk/tylerdoe/archives/results_ecoli_all_2024"
)

echo "=========================================="
echo "Datasets to analyze:"
for name in "${!DATASETS[@]}"; do
    dir="${DATASETS[$name]}"
    if [ -d "$dir" ]; then
        sample_count=$(find "$dir/amrfinder" -name "*_amr.tsv" 2>/dev/null | wc -l)
        prophage_count=$(find "$dir/vibrant" -name "*_phages.fna" 2>/dev/null | wc -l)
        echo "  ✓ $name: $sample_count samples, $prophage_count with prophages"
    else
        echo "  ✗ $name: Directory not found"
    fi
done
echo "=========================================="
echo ""

# Analyze each dataset
for name in "${!DATASETS[@]}"; do
    RESULTS_DIR="${DATASETS[$name]}"
    OUTPUT_DIR="$OUTPUT_BASE/$name"

    echo ""
    echo "=========================================="
    echo "Analyzing: $name"
    echo "=========================================="
    echo "Results directory: $RESULTS_DIR"
    echo "Output directory: $OUTPUT_DIR"
    echo ""

    # Check if directory exists
    if [ ! -d "$RESULTS_DIR" ]; then
        echo "⚠️  Directory not found, skipping..."
        continue
    fi

    # Create output directory
    mkdir -p "$OUTPUT_DIR"

    # Count samples
    SAMPLE_COUNT=$(find "$RESULTS_DIR/amrfinder" -name "*_amr.tsv" 2>/dev/null | wc -l)
    PROPHAGE_COUNT=$(find "$RESULTS_DIR/vibrant" -name "*_phages.fna" 2>/dev/null | wc -l)

    echo "Dataset: $name"
    echo "  Samples with AMR results: $SAMPLE_COUNT"
    echo "  Samples with prophage data: $PROPHAGE_COUNT"
    echo ""

    # ============================================================================
    # METHOD 1: Coordinate-Based Analysis
    # ============================================================================

    echo "Running Method 1: Coordinate-Based Analysis..."
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

    echo "Running Method 2: Annotation-Based Search..."
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
    # METHOD 3: Direct AMRFinder Scan
    # ============================================================================

    echo "Running Method 3: Direct AMRFinder Scan (this will take time)..."
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

done

echo ""
echo "=========================================="
echo "All Analyses Complete!"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "Results saved to: $OUTPUT_BASE"
echo ""
echo "Datasets analyzed:"
for name in "${!DATASETS[@]}"; do
    OUTPUT_DIR="$OUTPUT_BASE/$name"
    if [ -d "$OUTPUT_DIR" ]; then
        echo "  $name:"
        if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
            AMR_COUNT=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
                awk -F',' '$2 != "None" && $2 != ""' | wc -l)
            echo "    → $AMR_COUNT AMR genes found in prophages"
        fi
    fi
done
echo ""
echo "To view results:"
echo "  ls -lh $OUTPUT_BASE"
echo ""
echo "=========================================="

exit 0
