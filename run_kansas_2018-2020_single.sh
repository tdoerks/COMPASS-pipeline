#!/bin/bash
#SBATCH --job-name=compass_ks_2018-2020
#SBATCH --output=/fastscratch/tylerdoe/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Kansas 2018-2020"
echo "Processing all three years in one run"
echo "Organisms: Campylobacter, Salmonella, E. coli"
echo "State: Kansas only"
echo "Running from: /fastscratch/tylerdoe"
echo "Branch: v1.2-dev"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts with other runs
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_2018-2020

# Run pipeline for Kansas 2018-2020 NARMS data as a single run
# This will download metadata for all three years together
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2018 \
    --filter_year_end 2020 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_kansas_2018-2020 \
    -w work_2018-2020 \
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
    echo "Results location: /fastscratch/tylerdoe/results_kansas_2018-2020"
    echo ""
    echo "All samples from 2018, 2019, and 2020 processed together"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
