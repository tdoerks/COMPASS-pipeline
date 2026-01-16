#!/bin/bash
#SBATCH --job-name=hello_test
#SBATCH --output=hello_%j.out
#SBATCH --error=hello_%j.err
#SBATCH --time=00:02:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=100M

echo "Hello from SLURM!"
echo "Job ID: $SLURM_JOB_ID"
echo "Working directory: $(pwd)"
echo "Hostname: $(hostname)"
date
sleep 5
echo "Test complete!"
