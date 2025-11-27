#!/bin/bash
#SBATCH --job-name=compass_homes_test
#SBATCH --output=/homes/tylerdoe/slurm_homes_test_%j.out
#SBATCH --error=/homes/tylerdoe/slurm_homes_test_%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline Test - All from /homes/"
echo "Workaround for /fastscratch stale file handle issue"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Hostname: $(hostname)"
echo ""
echo "Configuration:"
echo "  Pipeline location: /homes/tylerdoe/pipelines/COMPASS-pipeline"
echo "  Work directory: /homes/tylerdoe/work_test"
echo "  Results directory: /homes/tylerdoe/results_test_5samples"
echo "  SLURM logs: /homes/tylerdoe/slurm_homes_test_${SLURM_JOB_ID}.out"
echo ""

# Change to homes pipeline directory
cd /homes/tylerdoe/pipelines/COMPASS-pipeline || {
    echo "ERROR: Cannot access /homes/tylerdoe/pipelines/COMPASS-pipeline"
    exit 1
}

echo "Current directory: $(pwd)"
echo ""

# Load Nextflow module
echo "Loading Nextflow module..."
module load Nextflow

# Verify Nextflow is available
if ! command -v nextflow &> /dev/null; then
    echo "ERROR: Nextflow not found after module load"
    exit 1
fi

echo "Nextflow version:"
nextflow -version
echo ""

# Set Nextflow home to homes
export NXF_HOME=/homes/tylerdoe/.nextflow_homes_test

echo "Running COMPASS pipeline with 5 E. coli 2024 samples..."
echo "Parameters:"
echo "  BioProject: PRJNA292663 (E. coli NARMS)"
echo "  Year: 2024"
echo "  Max samples: 5"
echo "  Skip BUSCO: yes (save time/space)"
echo ""

# Run pipeline with homes-only config (avoid /fastscratch mounts)
nextflow run main.nf \
    -profile beocat \
    -c nextflow_homes_only.config \
    --input_mode metadata \
    --bioproject "PRJNA292663" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --max_samples 5 \
    --skip_busco true \
    --outdir /homes/tylerdoe/results_test_5samples \
    -w /homes/tylerdoe/work_test \
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
    echo "Results location: /homes/tylerdoe/results_test_5samples"
    echo "Work directory: /homes/tylerdoe/work_test"
    echo ""
    echo "To view results:"
    echo "  ls -lh /homes/tylerdoe/results_test_5samples/summary/"
    echo ""
    echo "To clean up test data:"
    echo "  rm -rf /homes/tylerdoe/work_test"
    echo "  rm -rf /homes/tylerdoe/results_test_5samples"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Check logs:"
    echo "  tail -100 /homes/tylerdoe/slurm_homes_test_${SLURM_JOB_ID}.out"
    echo "  tail -100 /homes/tylerdoe/slurm_homes_test_${SLURM_JOB_ID}.err"
    echo "  cat .nextflow.log"
fi

exit $EXIT_CODE
