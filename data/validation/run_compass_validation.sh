#!/bin/bash
#SBATCH --job-name=compass_validation
#SBATCH --output=data/validation/compass_validation_%j.out
#SBATCH --error=data/validation/compass_validation_%j.err
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --partition=ksu-gen-highmem.q

# COMPASS Validation Run - ~200 Reference Genomes
# Date: 2026-02-05
# Pipeline: COMPASS v1.3-dev
# Expected runtime: 24-48 hours

set -e

echo "=========================================="
echo "COMPASS Validation Run"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: 64GB"
echo ""

# Load required modules
echo "Loading modules..."
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

# Set working directory
cd $SLURM_SUBMIT_DIR
echo "Working directory: $(pwd)"
echo ""

# Check samplesheet exists
SAMPLESHEET="data/validation/validation_samplesheet.csv"
if [ ! -f "$SAMPLESHEET" ]; then
    echo "ERROR: Samplesheet not found: $SAMPLESHEET"
    echo "Run: python data/validation/create_samplesheet.py"
    exit 1
fi

# Count samples
SAMPLE_COUNT=$(tail -n +2 "$SAMPLESHEET" | wc -l)
echo "Samplesheet: $SAMPLESHEET"
echo "Total samples: $SAMPLE_COUNT"
echo ""

# Set output directory
OUTDIR="data/validation/results"
echo "Output directory: $OUTDIR"
echo ""

# Run COMPASS pipeline
echo "=========================================="
echo "Starting COMPASS pipeline..."
echo "=========================================="
echo ""

nextflow run main.nf \
    -profile beocat \
    --input "$SAMPLESHEET" \
    --outdir "$OUTDIR" \
    --input_mode assembly \
    --max_cpus 16 \
    --max_memory 64.GB \
    -resume \
    -with-report "${OUTDIR}/nextflow_report.html" \
    -with-timeline "${OUTDIR}/nextflow_timeline.html" \
    -with-dag "${OUTDIR}/nextflow_dag.html"

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "COMPASS validation run completed successfully!"
    echo "=========================================="
    echo "End time: $(date)"
    echo "Results saved to: $OUTDIR"
    echo ""
    echo "Key outputs:"
    echo "  - AMR results: ${OUTDIR}/amrfinder/"
    echo "  - Prophage results: ${OUTDIR}/vibrant/"
    echo "  - Plasmid results: ${OUTDIR}/mobsuite/"
    echo "  - MLST results: ${OUTDIR}/mlst/"
    echo "  - MultiQC report: ${OUTDIR}/multiqc/multiqc_report.html"
    echo "  - Summary: ${OUTDIR}/summary/"
    echo ""
    echo "Next steps:"
    echo "  1. Review MultiQC report"
    echo "  2. Run validation analysis (future session)"
    echo "  3. Calculate sensitivity/specificity metrics"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "COMPASS validation run FAILED"
    echo "=========================================="
    echo "End time: $(date)"
    echo "Check error log: data/validation/compass_validation_${SLURM_JOB_ID}.err"
    echo ""
    exit 1
fi
