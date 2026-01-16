#!/bin/bash
#SBATCH --job-name=compass_ecoli_2023
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - E. coli 2023"
echo "Organism: E. coli only (PRJNA292663)"
echo "No state filter - ALL US samples"
echo "Year: 2023"
echo "Running from: /fastscratch/tylerdoe"
echo "Branch: v1.2-mod"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2023

# Run pipeline for E. coli 2023 NARMS data
# Note: Set filter_state to null to process ALL states
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state null \
    --filter_organism "Escherichia" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_ecoli_2023 \
    -w work_ecoli_2023 \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Pipeline completed successfully!"
    echo ""
    echo "Results location: /fastscratch/tylerdoe/results_ecoli_2023"
    echo ""
    echo "Summary report (if generated):"
    echo "  - /fastscratch/tylerdoe/results_ecoli_2023/summary/compass_summary.html"
    echo "  - /fastscratch/tylerdoe/results_ecoli_2023/summary/compass_summary.tsv"
    echo ""
    echo "Note: This includes ALL US E. coli 2023 samples"
    echo "Expected: ~500-1000 samples for 2023"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
