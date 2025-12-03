#!/bin/bash
#SBATCH --job-name=compass_ecoli_all_2024
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - All E. coli 2024"
echo "Organism: E. coli only (PRJNA292663)"
echo "No state filter - ALL US samples"
echo "Year: 2024"
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
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_all_2024

# Run pipeline for ALL E. coli 2024 NARMS data
# Note: Set filter_state to null to process ALL states
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state null \
    --filter_organism "Escherichia" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_ecoli_all_2024 \
    -w work_ecoli_all_2024 \
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
    echo "Results location: /fastscratch/tylerdoe/results_ecoli_all_2024"
    echo ""
    echo "Note: This includes ALL US E. coli 2024 samples (including KS)"
    echo "Kansas samples can be identified in downstream analysis"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
