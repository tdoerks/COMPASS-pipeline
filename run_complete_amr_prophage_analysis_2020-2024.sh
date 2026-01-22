#!/bin/bash
#SBATCH --job-name=complete_amr_prophage_2020-2024
#SBATCH --output=/homes/tylerdoe/slurm-complete-amr-prophage-2020-2024-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-complete-amr-prophage-2020-2024-%j.err
#SBATCH --time=96:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPLETE E. coli AMR-Prophage Analysis"
echo "2020-2024 (5-Year Dataset)"
echo "Method 3 (All Years) + Comprehensive Analysis"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_BASE="/homes/tylerdoe/complete_amr_prophage_analysis_2020-2024_$(date +%Y%m%d)"

# Create base output directory
mkdir -p "$OUTPUT_BASE"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Define datasets to analyze
declare -A DATASETS=(
    ["ecoli_2020"]="/bulk/tylerdoe/archives/ecoli_2020_all_narms"
    ["ecoli_2021"]="/bulk/tylerdoe/archives/kansas_2021_ecoli"
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

# Track overall statistics
TOTAL_AMR_GENES=0
declare -A YEAR_AMR_COUNTS

# ============================================================================
# PART 1: Run Method 3 on All Years (2020-2024)
# ============================================================================

echo ""
echo "=========================================="
echo "PART 1: METHOD 3 ANALYSIS (ALL YEARS)"
echo "=========================================="
echo ""

# Analyze each dataset
for name in ecoli_2020 ecoli_2021 ecoli_2022 ecoli_2023 ecoli_2024; do
    RESULTS_DIR="${DATASETS[$name]}"
    OUTPUT_DIR="$OUTPUT_BASE/$name"

    # Extract year from name
    YEAR=$(echo $name | grep -oP '\d{4}')

    echo ""
    echo "=========================================="
    echo "Analyzing: $name ($YEAR)"
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
    # METHOD 3: Direct AMRFinder Scan (GOLD STANDARD)
    # ============================================================================

    echo "Running Method 3: Direct AMRFinder Scan on $name..."
    echo "(Extracts prophage DNA and scans with AMRFinder)"
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
        echo "✅ Method 3 completed for $name in ${HOURS}h ${MINUTES}m"
        if [ -f "$OUTPUT_DIR/method3_direct_scan.csv" ]; then
            GENES_IN_PROPHAGE=$(tail -n +2 "$OUTPUT_DIR/method3_direct_scan.csv" | \
                awk -F',' '$2 != "None" && $2 != ""' | wc -l)
            echo "   AMR genes found in prophages: $GENES_IN_PROPHAGE"

            # Track statistics
            YEAR_AMR_COUNTS[$YEAR]=$GENES_IN_PROPHAGE
            TOTAL_AMR_GENES=$((TOTAL_AMR_GENES + GENES_IN_PROPHAGE))
        fi
    else
        echo "❌ Method 3 failed for $name"
        echo "   Check log: $OUTPUT_DIR/method3_direct_scan.log"
    fi
    echo ""

done

echo ""
echo "=========================================="
echo "PART 1 COMPLETE: Method 3 Analysis Done"
echo "=========================================="
echo ""
echo "Results by year:"
for year in 2020 2021 2022 2023 2024; do
    count=${YEAR_AMR_COUNTS[$year]:-0}
    echo "  $year: $count AMR genes in prophages"
done
echo ""
echo "Total AMR genes across all years: $TOTAL_AMR_GENES"
echo ""

# ============================================================================
# PART 2: Comprehensive Analysis on All 5 Years
# ============================================================================

echo ""
echo "=========================================="
echo "PART 2: COMPREHENSIVE ANALYSIS"
echo "=========================================="
echo ""

COMPREHENSIVE_OUTPUT="$OUTPUT_BASE/comprehensive"
mkdir -p "$COMPREHENSIVE_OUTPUT"

# Check that all CSVs exist
MISSING_CSV=0
for name in ecoli_2020 ecoli_2021 ecoli_2022 ecoli_2023 ecoli_2024; do
    CSV_FILE="$OUTPUT_BASE/$name/method3_direct_scan.csv"
    if [ ! -f "$CSV_FILE" ]; then
        echo "⚠️  Missing CSV: $CSV_FILE"
        MISSING_CSV=1
    fi
done

if [ $MISSING_CSV -eq 1 ]; then
    echo ""
    echo "❌ ERROR: Some Method 3 CSVs are missing"
    echo "   Cannot run comprehensive analysis"
    echo "   Check logs above for Method 3 failures"
    exit 1
fi

echo "All Method 3 CSVs found. Running comprehensive analysis..."
echo ""

# VIBRANT directories
VIBRANT_2020="/bulk/tylerdoe/archives/ecoli_2020_all_narms/vibrant"
VIBRANT_2021="/bulk/tylerdoe/archives/kansas_2021_ecoli/vibrant"
VIBRANT_2022="/bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant"
VIBRANT_2023="/bulk/tylerdoe/archives/results_ecoli_2023/vibrant"
VIBRANT_2024="/bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant"

START_TIME=$(date +%s)

./bin/analyze_amr_prophage_comprehensive.py \
    --csv-2020 "$OUTPUT_BASE/ecoli_2020/method3_direct_scan.csv" \
    --csv-2021 "$OUTPUT_BASE/ecoli_2021/method3_direct_scan.csv" \
    --csv-2022 "$OUTPUT_BASE/ecoli_2022/method3_direct_scan.csv" \
    --csv-2023 "$OUTPUT_BASE/ecoli_2023/method3_direct_scan.csv" \
    --csv-2024 "$OUTPUT_BASE/ecoli_2024/method3_direct_scan.csv" \
    --vibrant-2020 "$VIBRANT_2020" \
    --vibrant-2021 "$VIBRANT_2021" \
    --vibrant-2022 "$VIBRANT_2022" \
    --vibrant-2023 "$VIBRANT_2023" \
    --vibrant-2024 "$VIBRANT_2024" \
    --output-dir "$COMPREHENSIVE_OUTPUT" \
    --blast-samples 30

COMPREHENSIVE_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))

echo ""
if [ $COMPREHENSIVE_EXIT -eq 0 ]; then
    echo "✅ Comprehensive analysis completed in ${MINUTES} minutes"
else
    echo "❌ Comprehensive analysis failed"
    exit 1
fi

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo "=========================================="
echo "🎉 COMPLETE ANALYSIS FINISHED!"
echo "=========================================="
echo "End time: $(date)"
echo ""
echo "📁 Output Directory: $OUTPUT_BASE"
echo ""
echo "📊 Method 3 Results (by year):"
for year in 2020 2021 2022 2023 2024; do
    CSV="$OUTPUT_BASE/ecoli_$year/method3_direct_scan.csv"
    if [ -f "$CSV" ]; then
        COUNT=$(tail -n +2 "$CSV" | awk -F',' '$2 != "None" && $2 != ""' | wc -l)
        echo "   $year: $COUNT AMR genes in prophages"
    fi
done
echo ""
echo "📈 Comprehensive Analysis Output:"
echo "   Location: $COMPREHENSIVE_OUTPUT"
echo ""
echo "   Files created:"
echo "   - gene_frequency.csv          (AMR gene counts by year)"
echo "   - drug_class_trends.csv       (temporal trends 2020-2024)"
echo "   - top_samples.csv             (samples with most AMR genes)"
echo "   - gene_cooccurrence.csv       (genes found together)"
echo "   - prophage_characteristics.csv (size, GC content)"
echo "   - sequences_for_blast.fasta   (30 samples for validation)"
echo "   - summary_statistics.txt      (key findings)"
echo ""
echo "🧬 To view summary:"
echo "   cat $COMPREHENSIVE_OUTPUT/summary_statistics.txt"
echo ""
echo "📧 To send BLAST sequences to collaborator:"
echo "   File: $COMPREHENSIVE_OUTPUT/sequences_for_blast.fasta"
echo "   Size: $(ls -lh $COMPREHENSIVE_OUTPUT/sequences_for_blast.fasta 2>/dev/null | awk '{print $5}')"
echo ""
echo "🎓 Data ready for publication!"
echo ""
echo "=========================================="

exit 0
