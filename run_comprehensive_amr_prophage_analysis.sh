#!/bin/bash
#SBATCH --job-name=amr_prophage_comprehensive
#SBATCH --output=/homes/tylerdoe/slurm-amr-prophage-comprehensive-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-amr-prophage-comprehensive-%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Comprehensive AMR-Prophage Analysis"
echo "E. coli 2021-2024"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_DIR="/homes/tylerdoe/comprehensive_amr_prophage_analysis_$(date +%Y%m%d)"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Load required modules
echo "Loading BioPython module..."
module load Biopython/1.79-foss-2022a || {
    echo "❌ ERROR: Could not load BioPython"
    exit 1
}

# Verify Python can import Bio
python3 -c "from Bio import SeqIO; print('✅ BioPython import successful')" || {
    echo "❌ ERROR: BioPython module loaded but Python cannot import it"
    exit 1
}

echo ""
echo "Running comprehensive analysis..."
echo ""

# Run analysis
./bin/analyze_amr_prophage_comprehensive.py \
    --csv-2021 /homes/tylerdoe/ecoli_2021_prophage_amr_analysis_20260117/method3_direct_scan.csv \
    --csv-2022 /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2022/method3_direct_scan.csv \
    --csv-2023 /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2023/method3_direct_scan.csv \
    --csv-2024 /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2024/method3_direct_scan.csv \
    --vibrant-2021 /bulk/tylerdoe/archives/kansas_2021_ecoli/vibrant \
    --vibrant-2022 /bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant \
    --vibrant-2023 /bulk/tylerdoe/archives/results_ecoli_2023/vibrant \
    --vibrant-2024 /bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant \
    --output-dir "$OUTPUT_DIR" \
    --blast-samples 30

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ ANALYSIS COMPLETE!"
    echo "=========================================="
    echo ""
    echo "📁 Results saved to: $OUTPUT_DIR"
    echo ""
    echo "📊 Files generated:"
    echo "   - gene_frequency.csv          (AMR gene counts by year)"
    echo "   - drug_class_trends.csv       (Drug class temporal patterns)"
    echo "   - top_samples.csv             (Samples with most genes)"
    echo "   - gene_cooccurrence.csv       (Genes appearing together)"
    echo "   - prophage_characteristics.csv (Size, GC content stats)"
    echo "   - sequences_for_blast.fasta   (30 sequences for BLAST validation)"
    echo "   - summary_statistics.txt      (Key numbers for publication)"
    echo ""
    echo "🧬 Next steps:"
    echo "   1. Review summary_statistics.txt"
    echo "   2. BLAST sequences_for_blast.fasta against phage database"
    echo "   3. Use CSV files to create publication figures"
    echo "   4. Include analyses in manuscript"
else
    echo "❌ ANALYSIS FAILED"
    echo "=========================================="
    echo "Check error messages above"
fi

echo ""
echo "End time: $(date)"
echo "=========================================="

exit $EXIT_CODE
