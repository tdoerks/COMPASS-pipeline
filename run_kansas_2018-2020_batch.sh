#!/bin/bash
# Batch submission script for Kansas 2018-2020 NARMS data
# Submits all three years as separate SLURM jobs

echo "=========================================="
echo "COMPASS Pipeline - Batch Submission"
echo "Submitting Kansas 2018, 2019, and 2020"
echo "=========================================="
echo ""

# Navigate to pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Pull latest code
echo "Pulling latest v1.2-dev code..."
git pull origin v1.2-dev
echo ""

# Submit 2018
echo "Submitting 2018..."
JOB_2018=$(sbatch run_kansas_2018_fastscratch.sh | awk '{print $4}')
echo "Job 2018: $JOB_2018"

# Submit 2019
echo "Submitting 2019..."
JOB_2019=$(sbatch run_kansas_2019_fastscratch.sh | awk '{print $4}')
echo "Job 2019: $JOB_2019"

# Submit 2020
echo "Submitting 2020..."
JOB_2020=$(sbatch run_kansas_2020_fastscratch.sh | awk '{print $4}')
echo "Job 2020: $JOB_2020"

echo ""
echo "=========================================="
echo "All jobs submitted!"
echo "2018: $JOB_2018"
echo "2019: $JOB_2019"
echo "2020: $JOB_2020"
echo "=========================================="
echo ""
echo "Monitor with: squeue -u tylerdoe"
echo "Follow logs with: tail -f /fastscratch/tylerdoe/slurm-JOBID.out"
