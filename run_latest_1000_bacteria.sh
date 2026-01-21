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

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline || {
    echo "ERROR: Could not cd to /fastscratch/tylerdoe/COMPASS-pipeline"
    exit 1
}

# Load Nextflow
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_latest_1000

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/latest_1000_bacteria_$(date +%Y%m%d)"

echo "Working directory: $(pwd)"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Run pipeline for latest 1000 bacterial genomes
# No organism filter - gets all bacteria
# Platform and library source filters ensure quality isolate data
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_platform "ILLUMINA" \
    --filter_library_source "GENOMIC" \
    --max_samples 1000 \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "$OUTPUT_DIR" \
    -w work_latest_1000 \
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
    echo "Results location: $OUTPUT_DIR"
    echo ""
    echo "Summary Report:"
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
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs:"
    echo "  - /homes/tylerdoe/slurm-compass-latest-1000-${SLURM_JOB_ID}.out"
    echo "  - .nextflow.log"
fi

exit $EXIT_CODE
