#!/bin/bash
#SBATCH --job-name=kansas_2023
#SBATCH --output=kansas_2023_%j.out
#SBATCH --error=kansas_2023_%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Load Nextflow
module load Nextflow

# Run full Kansas pipeline for 2023 only
nextflow run main_metadata.nf \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --outdir results_kansas_2023
