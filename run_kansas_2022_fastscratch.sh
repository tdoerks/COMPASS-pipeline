#!/bin/bash
#SBATCH --job-name=compass_ecoli_2022
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - E. coli 2022"
echo "Organism: E. coli only (PRJNA292663)"
echo "No state filter - ALL US samples"
echo "Year: 2022"
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
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2022

# Run pipeline for E. coli 2022 NARMS data
# Note: Set filter_state to null to process ALL states
# Uses v1.2-mod branch which has error handling for failed assemblies
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state null \
    --filter_organism "Escherichia" \
    --filter_year_start 2022 \
    --filter_year_end 2022 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/kansas_2022_ecoli \
    -w work_ecoli_2022 \
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
    echo "Results location: /fastscratch/tylerdoe/kansas_2022_ecoli"
    echo ""
    echo "Summary report (if generated):"
    echo "  - /fastscratch/tylerdoe/kansas_2022_ecoli/summary/compass_summary.html"
    echo "  - /fastscratch/tylerdoe/kansas_2022_ecoli/summary/compass_summary.tsv"
    echo ""
    echo "Note: This includes ALL US E. coli 2022 samples"
    echo "Expected: ~500-1000 samples for 2022"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
