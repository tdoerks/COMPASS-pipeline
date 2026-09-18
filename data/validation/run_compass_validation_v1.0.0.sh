#!/bin/bash
#SBATCH --job-name=compass_val_v1.0.0
#SBATCH --output=/scratch/tylerdoe/COMPASS_Validation_Results_v1.0.0_%j/logs/compass_validation_%j.out
#SBATCH --error=/scratch/tylerdoe/COMPASS_Validation_Results_v1.0.0_%j/logs/compass_validation_%j.err
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# COMPASS v1.0.0 Validation Run
# Comparison validation against v1.3-dev results from 2026-02-09
# Date: 2026-03-07
# Expected runtime: 24-48 hours

set -e

echo "=========================================="
echo "COMPASS v1.0.0 Validation Run"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: 64GB"
echo "Pipeline Version: 1.0.0"
echo ""

# Load required modules
echo "Loading modules..."
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

# Change to COMPASS pipeline directory
# NOTE: Assumes you have checked out the test-validation-1.0.0 branch
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
if [ ! -d "$PIPELINE_DIR" ]; then
    echo "ERROR: Pipeline directory not found: $PIPELINE_DIR"
    echo "Please ensure you have cloned the repository to /fastscratch/tylerdoe/COMPASS-pipeline"
    echo "and checked out the test-validation-1.0.0 branch"
    exit 1
fi

cd "$PIPELINE_DIR" || exit 1
echo "Working directory: $(pwd)"
echo ""

# Verify we're on the correct branch/tag
CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || echo "unknown")
echo "Git version: $CURRENT_VERSION"
echo ""

# Check samplesheet exists
# NOTE: You'll need to update this path to point to your validation genomes
SAMPLESHEET="$PIPELINE_DIR/data/validation/validation_samplesheet_fasta.csv"
if [ ! -f "$SAMPLESHEET" ]; then
    echo "ERROR: Samplesheet not found: $SAMPLESHEET"
    echo ""
    echo "Available samplesheets in data/validation/:"
    ls -lh "$PIPELINE_DIR/data/validation/"*samplesheet*.csv 2>/dev/null || echo "  (none found)"
    echo ""
    echo "Please create or specify the correct samplesheet path."
    echo "The samplesheet should have columns: sample,organism,fasta"
    exit 1
fi

# Count samples
SAMPLE_COUNT=$(tail -n +2 "$SAMPLESHEET" | wc -l)
echo "Samplesheet: $SAMPLESHEET"
echo "Total samples: $SAMPLE_COUNT"
echo ""

# Set output directory with job ID
OUTDIR="/scratch/tylerdoe/COMPASS_Validation_Results_v1.0.0_${SLURM_JOB_ID}"
mkdir -p "$OUTDIR/logs"
echo "Output directory: $OUTDIR"
echo ""

# Run COMPASS v1.0.0 pipeline
echo "=========================================="
echo "Starting COMPASS v1.0.0 pipeline..."
echo "=========================================="
echo ""

nextflow run main.nf \
    -profile beocat \
    --input "$SAMPLESHEET" \
    --outdir "${OUTDIR}/results" \
    --input_mode fasta \
    --max_cpus 16 \
    --max_memory 64.GB \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    -resume \
    -with-report "${OUTDIR}/results/nextflow_report.html" \
    -with-timeline "${OUTDIR}/results/nextflow_timeline.html" \
    -with-dag "${OUTDIR}/results/nextflow_dag.html"

EXIT_CODE=$?

# Check exit status
if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "COMPASS v1.0.0 validation run completed successfully!"
    echo "=========================================="
    echo "End time: $(date)"
    echo "Results saved to: $OUTDIR"
    echo ""
    echo "Key outputs:"
    echo "  - AMR results: ${OUTDIR}/results/amrfinder/"
    echo "  - Prophage results: ${OUTDIR}/results/vibrant/"
    echo "  - Plasmid results: ${OUTDIR}/results/mobsuite/"
    echo "  - MLST results: ${OUTDIR}/results/mlst/"
    echo "  - MultiQC report: ${OUTDIR}/results/multiqc/multiqc_report.html"
    echo "  - Summary: ${OUTDIR}/results/summary/"
    echo ""
    echo "Comparison with v1.3-dev:"
    echo "  v1.3-dev results: /scratch/tylerdoe/COMPASS_Validation_Results_v1.3-dev_2026-02-09/"
    echo "  v1.0.0 results:   $OUTDIR"
    echo ""
    echo "Next steps:"
    echo "  1. Review MultiQC report"
    echo "  2. Compare results between v1.0.0 and v1.3-dev"
    echo "  3. Document differences in tool outputs"
    echo "  4. Calculate sensitivity/specificity metrics"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "COMPASS v1.0.0 validation run FAILED"
    echo "=========================================="
    echo "End time: $(date)"
    echo "Exit code: $EXIT_CODE"
    echo "Check error log: ${OUTDIR}/logs/compass_validation_${SLURM_JOB_ID}.err"
    echo ""
    exit 1
fi
