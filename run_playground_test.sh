#!/bin/bash
#SBATCH --job-name=compass_playground
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "Starting COMPASS pipeline - claude-dev-playground branch"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"

module load Nextflow

# Test with 5 Kansas 2023 samples
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --max_samples 5 \
    --skip_busco true \
    --outdir results_playground_test \
    -resume

echo "End time: $(date)"
