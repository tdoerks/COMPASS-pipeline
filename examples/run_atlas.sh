#!/bin/bash
#SBATCH --job-name=COMPASS
#SBATCH --partition=atlas
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=48:00:00
#SBATCH --output=logs/compass_%j.out
#SBATCH --error=logs/compass_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=your.email@usda.gov

###############################################################################
# COMPASS Pipeline - Atlas Submission Script
###############################################################################
# USDA SCINet Atlas HPC Cluster
# https://scinet.usda.gov/guides/resources/atlas
#
# This script submits the COMPASS pipeline to SLURM on Atlas.
# The main Nextflow process runs with minimal resources, while individual
# pipeline processes are submitted as separate SLURM jobs.
###############################################################################

# Exit on error
set -e

# Load required modules
module purge
module load nextflow
module load apptainer

# Create logs directory
mkdir -p logs

# Set up environment
export NXF_OPTS='-Xms1g -Xmx4g'
export NXF_SINGULARITY_CACHEDIR="$TMPDIR/.apptainer/cache"
export APPTAINER_CACHEDIR="$TMPDIR/.apptainer/cache"

# Pipeline parameters
INPUT="samplesheet.csv"
OUTDIR="results"
WORK_DIR="$TMPDIR/work"

# Database paths (update these to your paths)
CHECKV_DB="/path/to/checkv-db-v1.5"

# Optional: Set prophage_db if you have it pre-downloaded
# PROPHAGE_DB="/path/to/prophage_db.dmnd"

# NARMS filtering parameters (optional)
FILTER_STATE="KS"
FILTER_YEAR_START="2020"
FILTER_YEAR_END="2023"

# Print job information
echo "================================================"
echo "COMPASS Pipeline - Atlas"
echo "================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Running on: $(hostname)"
echo "Working directory: $(pwd)"
echo "Temp directory: $TMPDIR"
echo "================================================"

# Run the pipeline
nextflow run main.nf \
    -profile atlas \
    --input ${INPUT} \
    --outdir ${OUTDIR} \
    --checkv_db ${CHECKV_DB} \
    --filter_state ${FILTER_STATE} \
    --filter_year_start ${FILTER_YEAR_START} \
    --filter_year_end ${FILTER_YEAR_END} \
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
