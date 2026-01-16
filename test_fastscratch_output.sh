#!/bin/bash
#SBATCH --job-name=test_fastscratch_output
#SBATCH --output=/fastscratch/tylerdoe/TEST_slurm_%j.out
#SBATCH --error=/fastscratch/tylerdoe/TEST_slurm_%j.err
#SBATCH --time=00:02:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=100M

echo "=========================================="
echo "Testing SLURM Output to /fastscratch/"
echo "=========================================="
echo "If you see this, SLURM CAN write to /fastscratch!"
echo "Job ID: $SLURM_JOB_ID"
echo "Working directory: $(pwd)"
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "=========================================="
