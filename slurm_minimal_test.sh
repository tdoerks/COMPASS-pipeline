#!/bin/bash
#SBATCH --job-name=minimal_test
#SBATCH --time=00:01:00
#SBATCH --mem=1G
#SBATCH --output=/fastscratch/tylerdoe/minimal_test_%j.out
#SBATCH --error=/fastscratch/tylerdoe/minimal_test_%j.err

echo "=========================================="
echo "Minimal Slurm Test - Beocat Status Check"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Hostname: $(hostname)"
echo ""

echo "✅ If you see this, Slurm is working!"
echo ""
echo "System info:"
echo "  - User: $USER"
echo "  - Working directory: $PWD"
echo "  - Slurm job name: $SLURM_JOB_NAME"
echo "  - Allocated memory: $SLURM_MEM_PER_NODE MB"
echo ""

echo "End time: $(date)"
echo "=========================================="
