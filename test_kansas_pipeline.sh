#!/bin/bash
#SBATCH --job-name=compass_kansas_test
#SBATCH --output=test_kansas_%j.out
#SBATCH --error=test_kansas_%j.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Load Nextflow
module load Nextflow

# Run full pipeline from metadata filtering to results
nextflow run main_metadata.nf \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --outdir test_kansas_2023
