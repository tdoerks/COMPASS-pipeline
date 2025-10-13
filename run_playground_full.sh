#!/bin/bash
#SBATCH --job-name=compass_playground_full
#SBATCH --output=compass_playground_full_%j.out
#SBATCH --error=compass_playground_full_%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "Starting COMPASS pipeline - Full Kansas 2023 dataset"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"

module load Nextflow

# Full Kansas 2023 dataset with all new analysis features
nextflow run main_metadata.nf \
    -profile beocat \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --outdir results_playground_ks2023_full \
    -resume

echo "End time: $(date)"
