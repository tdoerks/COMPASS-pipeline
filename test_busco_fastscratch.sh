#!/bin/bash
#SBATCH --job-name=test_busco
#SBATCH --output=/homes/tylerdoe/test_busco_%j.out
#SBATCH --error=/homes/tylerdoe/test_busco_%j.err
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Testing BUSCO Integration - v1.2-dev"
echo "5 samples from Kansas 2024"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Test with just 5 Kansas 2024 samples
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --max_samples 5 \
    --skip_busco false \
    --outdir /fastscratch/tylerdoe/test_busco_results \
    -w work_busco_test \
    -name busco_test_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ BUSCO test completed successfully!"
    echo ""
    echo "Check results:"
    echo "  ls /fastscratch/tylerdoe/test_busco_results/busco/"
    echo ""
    echo "Expected: 5 BUSCO result directories"
else
    echo "❌ BUSCO test failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
