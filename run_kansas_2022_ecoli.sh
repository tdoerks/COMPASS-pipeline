#!/bin/bash

#SBATCH --job-name=ks_ecoli_2022
#SBATCH --output=/fastscratch/tylerdoe/logs/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/logs/slurm-%j.err
#SBATCH --partition=batch.q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=96:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Kansas 2022 E. coli NARMS Analysis
# E. coli BioProject: PRJNA292663
# Year: 2022
# State filter: KS (Kansas)

echo "=========================================="
echo "COMPASS Pipeline - Kansas 2022 E. coli"
echo "=========================================="
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start time: $(date)"
echo ""
echo "Parameters:"
echo "  - BioProject: PRJNA292663 (E. coli NARMS)"
echo "  - Year: 2022"
echo "  - State: Kansas (KS)"
echo "  - Output: kansas_2022_ecoli"
echo ""

# Create logs directory if it doesn't exist
mkdir -p /fastscratch/tylerdoe/logs

# Load required modules
module load Nextflow

# Navigate to pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Ensure we're in the right directory
pwd
ls -la main.nf

# Run the pipeline
nextflow run main.nf \
    --input_mode metadata \
    --bioproject "PRJNA292663" \
    --filter_state "KS" \
    --filter_year_start 2022 \
    --filter_year_end 2022 \
    --outdir /fastscratch/tylerdoe/kansas_2022_ecoli \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Pipeline completed successfully!"
    echo ""
    echo "Results directory:"
    echo "  /fastscratch/tylerdoe/kansas_2022_ecoli"
    echo ""
    echo "Key outputs:"
    echo "  - Metadata: kansas_2022_ecoli/metadata/"
    echo "  - Assemblies: kansas_2022_ecoli/assemblies/"
    echo "  - AMR results: kansas_2022_ecoli/amrfinder/"
    echo "  - MLST: kansas_2022_ecoli/mlst/"
    echo "  - Phage: kansas_2022_ecoli/vibrant/"
    echo "  - Summary: kansas_2022_ecoli/summary/"
    echo ""
else
    echo ""
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Check logs:"
    echo "  - SLURM log: /fastscratch/tylerdoe/logs/slurm-${SLURM_JOB_ID}.out"
    echo "  - Nextflow log: /fastscratch/tylerdoe/COMPASS-pipeline/.nextflow.log"
    echo ""
    echo "To resume from where it failed:"
    echo "  cd /fastscratch/tylerdoe/COMPASS-pipeline"
    echo "  sbatch run_kansas_2022_ecoli.sh"
    echo ""
fi

exit $EXIT_CODE
