#!/bin/bash
#SBATCH --job-name=ecoli_2020
#SBATCH --output=ecoli_2020_%j.out
#SBATCH --error=ecoli_2020_%j.err
#SBATCH --time=84:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Load Nextflow
module load Nextflow

# Run COMPASS pipeline for 2020 E. coli only
# Time allocation: 84 hours (3.5 days) to complete before maintenance window
# Maintenance starts: January 13, 2026 at 08:00:00
nextflow run main_metadata.nf \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --filter_year_end 2020 \
    --outdir results_ecoli_2020
