#!/bin/bash
#SBATCH --job-name=compass_latest_1000
#SBATCH --output=/homes/tylerdoe/slurm-compass-latest-1000-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-compass-latest-1000-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Latest 1000 Bacteria"
echo "All bacterial species from recent NCBI submissions"
echo "Platform: Illumina only"
echo "Library: GENOMIC (isolates)"
echo "No organism filter - Maximum diversity!"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set working directory
WORK_DIR="/fastscratch/tylerdoe"
OUTPUT_DIR="${WORK_DIR}/latest_1000_bacteria_$(date +%Y%m%d)"

cd "$WORK_DIR" || {
    echo "ERROR: Could not cd to $WORK_DIR"
    exit 1
}

echo "Working directory: $WORK_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Clean up any existing work directory from previous runs
if [ -d "work" ]; then
    echo "Cleaning up previous work directory..."
    rm -rf work
fi

# Load required modules
echo "Loading required modules..."
module load Nextflow/24.04.2 || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

module load Singularity/3.11.4 || {
    echo "WARNING: Could not load Singularity, trying without module"
}

echo ""
echo "Nextflow version:"
nextflow -version
echo ""

# Set Nextflow configuration
export NXF_SINGULARITY_CACHEDIR="/fastscratch/tylerdoe/singularity_cache"
export NXF_OPTS="-Xms512M -Xmx4G"

# Ensure cache directory exists
mkdir -p "$NXF_SINGULARITY_CACHEDIR"

echo "Running COMPASS pipeline..."
echo ""

# Run pipeline
nextflow run /fastscratch/tylerdoe/COMPASS-pipeline/main.nf \
    -profile beocat \
    --all_bacterial true \
    --filter_platform "ILLUMINA" \
    --filter_library_source "GENOMIC" \
    --max_samples 1000 \
    --outdir "$OUTPUT_DIR" \
    --cpus 8 \
    --memory "32 GB" \
    -resume \
    -with-report "${OUTPUT_DIR}/nextflow_report.html" \
    -with-timeline "${OUTPUT_DIR}/nextflow_timeline.html" \
    -with-dag "${OUTPUT_DIR}/nextflow_dag.html"

EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ COMPASS PIPELINE COMPLETE!"
    echo "=========================================="
    echo ""
    echo "Results location: $OUTPUT_DIR"
    echo "  - ${OUTPUT_DIR}/summary/compass_summary.html"
    echo "  - ${OUTPUT_DIR}/summary/compass_summary.tsv"
    echo ""
    echo "Note: This dataset includes a diverse mix of bacterial species"
    echo "      from the 1000 most recently submitted samples on NCBI SRA."
    echo ""
    echo "Expected diversity:"
    echo "  - Clinical pathogens (E. coli, Salmonella, Staph, etc.)"
    echo "  - Environmental isolates"
    echo "  - Food/agricultural bacteria"
    echo "  - Marine and soil bacteria"
    echo "  - And many more!"
    echo ""
    echo "Use the Data Explorer to browse by organism, view AMR patterns,"
    echo "and explore prophage diversity across bacterial species."
else
    echo "❌ PIPELINE FAILED"
    echo "=========================================="
    echo "Check error logs above for details"
fi

echo ""
echo "End time: $(date)"
echo "=========================================="

exit $EXIT_CODE
