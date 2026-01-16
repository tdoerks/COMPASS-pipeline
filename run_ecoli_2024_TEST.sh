#!/bin/bash
#SBATCH --job-name=compass_ecoli_2024_test
#SBATCH --output=/fastscratch/tylerdoe/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - All E. coli 2024 TEST"
echo "Testing original working script"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Initial working directory: $(pwd)"
echo ""

# Try to find the correct directory name
if [ -d "/fastscratch/tylerdoe/COMPASS-pipeline" ]; then
    COMPASS_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
    echo "✅ Found COMPASS-pipeline (uppercase)"
elif [ -d "/fastscratch/tylerdoe/compass-pipeline" ]; then
    COMPASS_DIR="/fastscratch/tylerdoe/compass-pipeline"
    echo "✅ Found compass-pipeline (lowercase)"
else
    echo "❌ ERROR: Cannot find COMPASS pipeline directory!"
    echo "Checked:"
    echo "  - /fastscratch/tylerdoe/COMPASS-pipeline"
    echo "  - /fastscratch/tylerdoe/compass-pipeline"
    ls -ld /fastscratch/tylerdoe/*compass* 2>&1 || echo "  No compass directories found"
    exit 1
fi

echo "Using directory: $COMPASS_DIR"
cd "$COMPASS_DIR" || exit 1

echo "Current directory after cd: $(pwd)"
echo ""

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2024_test

echo "Running pipeline with these settings:"
echo "  - Organism: E. coli (all NARMS 2024)"
echo "  - States: ALL (no filter)"
echo "  - Year: 2024"
echo "  - Output: /fastscratch/tylerdoe/results_ecoli_2024_test"
echo ""

# Run pipeline for ALL E. coli 2024 NARMS data
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --bioproject "PRJNA292663" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_ecoli_2024_test \
    -w /fastscratch/tylerdoe/work_ecoli_2024_test \
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
    echo "Results location: /fastscratch/tylerdoe/results_ecoli_2024_test"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs:"
    echo "  - SLURM log: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out"
    echo "  - Nextflow log: ${COMPASS_DIR}/.nextflow.log"
fi

exit $EXIT_CODE
