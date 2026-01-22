#!/bin/bash
#SBATCH --job-name=amr_prophage_comprehensive_2020-2024
#SBATCH --output=/homes/tylerdoe/slurm-amr-prophage-comprehensive-2020-2024-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-amr-prophage-comprehensive-2020-2024-%j.err
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Comprehensive AMR-Prophage Analysis"
echo "E. coli 2020-2024 (5-Year Dataset)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_DIR="/homes/tylerdoe/comprehensive_amr_prophage_analysis_2020-2024_$(date +%Y%m%d)"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Find latest directories for each year
# Use glob pattern to find most recent analysis directories
CSV_2020=$(ls -t /homes/tylerdoe/ecoli_2020_prophage_amr_analysis_*/method3_direct_scan.csv 2>/dev/null | head -1)
CSV_2021=$(ls -t /homes/tylerdoe/ecoli_2021_prophage_amr_analysis_*/method3_direct_scan.csv 2>/dev/null | head -1)
CSV_2022=$(ls -t /homes/tylerdoe/ecoli_prophage_amr_analysis_*/ecoli_2022/method3_direct_scan.csv 2>/dev/null | head -1)
CSV_2023=$(ls -t /homes/tylerdoe/ecoli_prophage_amr_analysis_*/ecoli_2023/method3_direct_scan.csv 2>/dev/null | head -1)
CSV_2024=$(ls -t /homes/tylerdoe/ecoli_prophage_amr_analysis_*/ecoli_2024/method3_direct_scan.csv 2>/dev/null | head -1)

echo "Method 3 CSV files:"
echo "  2020: ${CSV_2020:-NOT FOUND}"
echo "  2021: ${CSV_2021:-NOT FOUND}"
echo "  2022: ${CSV_2022:-NOT FOUND}"
echo "  2023: ${CSV_2023:-NOT FOUND}"
echo "  2024: ${CSV_2024:-NOT FOUND}"
echo ""

# Check required files
MISSING=0
for year in 2021 2022 2023 2024; do
    var_name="CSV_$year"
    if [ -z "${!var_name}" ]; then
        echo "❌ ERROR: No Method 3 CSV found for $year"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "Please run AMR-prophage analysis for missing years first"
    exit 1
fi

# 2020 is optional
if [ -z "$CSV_2020" ]; then
    echo "⚠️  Warning: No 2020 data found - running with 2021-2024 only"
    echo "   To include 2020, run: sbatch run_ecoli_2020_prophage_amr_analysis.sh"
    echo ""
fi

# VIBRANT directories
VIBRANT_2020="/bulk/tylerdoe/archives/ecoli_2020_all_narms/vibrant"
VIBRANT_2021="/bulk/tylerdoe/archives/kansas_2021_ecoli/vibrant"
VIBRANT_2022="/bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant"
VIBRANT_2023="/bulk/tylerdoe/archives/results_ecoli_2023/vibrant"
VIBRANT_2024="/bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant"

echo "VIBRANT directories:"
for year in 2020 2021 2022 2023 2024; do
    var_name="VIBRANT_$year"
    dir="${!var_name}"
    if [ -d "$dir" ]; then
        count=$(find "$dir" -name "*_phages.fna" 2>/dev/null | wc -l)
        echo "  $year: $dir ($count prophage files)"
    else
        echo "  $year: $dir (NOT FOUND)"
    fi
done
echo ""

echo "Output directory: $OUTPUT_DIR"
echo ""

# Build command with optional 2020 data
CMD="./bin/analyze_amr_prophage_comprehensive.py"

if [ -n "$CSV_2020" ] && [ -d "$VIBRANT_2020" ]; then
    echo "✅ Including 2020 data in analysis"
    CMD="$CMD --csv-2020 $CSV_2020 --vibrant-2020 $VIBRANT_2020"
fi

CMD="$CMD \
    --csv-2021 $CSV_2021 \
    --csv-2022 $CSV_2022 \
    --csv-2023 $CSV_2023 \
    --csv-2024 $CSV_2024 \
    --vibrant-2021 $VIBRANT_2021 \
    --vibrant-2022 $VIBRANT_2022 \
    --vibrant-2023 $VIBRANT_2023 \
    --vibrant-2024 $VIBRANT_2024 \
    --output-dir $OUTPUT_DIR \
    --blast-samples 30"

echo "Running comprehensive analysis..."
echo ""
echo "=========================================="
echo ""

$CMD

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Comprehensive analysis completed successfully!"
    echo ""
    echo "Results location: $OUTPUT_DIR"
    echo ""
    echo "Output files:"
    echo "  - gene_frequency.csv"
    echo "  - drug_class_trends.csv"
    echo "  - top_samples.csv"
    echo "  - gene_cooccurrence.csv"
    echo "  - prophage_characteristics.csv"
    echo "  - sequences_for_blast.fasta  (ready for collaborator!)"
    echo "  - summary_statistics.txt"
    echo ""
    echo "To view summary:"
    echo "  cat $OUTPUT_DIR/summary_statistics.txt"
    echo ""
    echo "🧬 Data ready for publication!"
else
    echo "❌ Analysis failed with exit code $EXIT_CODE"
    echo "Check logs for details"
fi

exit $EXIT_CODE
