#!/bin/bash
#SBATCH --job-name=kansas_2025
#SBATCH --output=kansas_2025_%j.out
#SBATCH --error=kansas_2025_%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Load Nextflow
module load Nextflow

# Run full Kansas pipeline for 2025 only
nextflow run main_metadata.nf \
    --filter_state "KS" \
    --filter_year_start 2025 \
    --filter_year_end 2025 \
    --outdir results_kansas_2025
