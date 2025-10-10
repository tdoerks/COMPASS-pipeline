#!/bin/bash
#SBATCH --job-name=COMPASS
#SBATCH --partition=batch.q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=48:00:00
#SBATCH --output=logs/compass_%j.out
#SBATCH --error=logs/compass_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=your.email@ksu.edu

###############################################################################
# COMPASS Pipeline - Beocat Submission Script
###############################################################################
# Kansas State University Beocat HPC Cluster
# https://www.cis.ksu.edu/beocat
#
# This script submits the COMPASS pipeline to SLURM on Beocat.
# The main Nextflow process runs on the login/submit node with minimal
# resources, while individual pipeline processes are submitted as separate
# SLURM jobs with their own resource requirements.
###############################################################################

# Exit on error
set -e

# Load required modules
module purge
module load Nextflow/24.04.0
module load Apptainer/1.2.5

# Create logs directory
mkdir -p logs

# Set up environment
export NXF_OPTS='-Xms1g -Xmx4g'
export NXF_SINGULARITY_CACHEDIR="$HOME/.apptainer/cache"

# Pipeline parameters
INPUT="samplesheet.csv"
OUTDIR="results"
WORK_DIR="work"

# Database paths (update these to your paths)
CHECKV_DB="/homes/tylerdoe/databases/checkv-db-v1.5"

# Optional: Set prophage_db if you have it pre-downloaded
# PROPHAGE_DB="/homes/tylerdoe/databases/prophage_db.dmnd"

# Print job information
echo "================================================"
echo "COMPASS Pipeline - Beocat"
echo "================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Running on: $(hostname)"
echo "Working directory: $(pwd)"
echo "================================================"

# Run the pipeline
nextflow run main.nf \
    -profile beocat \
    --input ${INPUT} \
    --outdir ${OUTDIR} \
    --checkv_db ${CHECKV_DB} \
    -work-dir ${WORK_DIR} \
    -resume

# Capture exit code
EXIT_CODE=$?

# Print completion information
echo "================================================"
echo "Pipeline finished with exit code: $EXIT_CODE"
echo "End time: $(date)"
echo "================================================"

# Cleanup work directory (optional - comment out to keep)
# if [ $EXIT_CODE -eq 0 ]; then
#     echo "Cleaning up work directory..."
#     rm -rf ${WORK_DIR}
# fi

exit $EXIT_CODE
