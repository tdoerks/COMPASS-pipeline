#!/bin/bash
#SBATCH --job-name=test_minimal
#SBATCH --output=test_minimal_%j.out
#SBATCH --error=test_minimal_%j.err
#SBATCH --time=00:05:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G

echo "=========================================="
echo "Minimal SLURM Test"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Working directory: $(pwd)"
echo "Start time: $(date)"
echo "Hostname: $(hostname)"
echo ""

# Test module loading
echo "Testing module load..."
module load Nextflow
echo "Nextflow module loaded successfully"
echo ""

# Check Nextflow version
echo "Nextflow version:"
nextflow -version
echo ""

echo "End time: $(date)"
echo "=========================================="
echo "Test completed successfully!"
