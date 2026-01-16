#!/bin/bash
#SBATCH --job-name=test_mobsuite_fix
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "MOB-suite Fix Test - 5 E. coli Samples"
echo "Testing plasmid detection after bug fix"
echo "Running from: /homes/tylerdoe"
echo "Branch: v1.2-dev (with MOB-suite fix)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to homes directory for test
cd /homes/tylerdoe/pipelines/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Set unique Nextflow home for this test
export NXF_HOME=/homes/tylerdoe/.nextflow_mobsuite_test

# Run pipeline on just 5 E. coli 2024 samples as a test
# This will test if MOB-suite now properly detects plasmids
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state null \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --max_samples 5 \
    --skip_busco true \
    --outdir /homes/tylerdoe/test_mobsuite_fix_results \
    -w work_mobsuite_test \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test completed successfully!"
    echo ""
    echo "Results location: /homes/tylerdoe/test_mobsuite_fix_results"
    echo ""
    echo "Check MOB-suite results:"
    echo "  ls /homes/tylerdoe/test_mobsuite_fix_results/mobsuite/"
    echo ""
    echo "Check for plasmid files:"
    echo "  find /homes/tylerdoe/test_mobsuite_fix_results/mobsuite/ -name 'plasmid_*.fasta'"
    echo ""
    echo "Count plasmids found:"
    echo "  grep -v '^sample_id' /homes/tylerdoe/test_mobsuite_fix_results/mobsuite/*/mobtyper_results.txt"
else
    echo "❌ Test failed with exit code $EXIT_CODE"
    echo "Check logs: /homes/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
