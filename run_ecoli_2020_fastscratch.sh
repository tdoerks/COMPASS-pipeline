#!/bin/bash
#SBATCH --job-name=compass_ecoli_2020
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - E. coli 2020"
echo "Organism: E. coli only (PRJNA292663)"
echo "No state filter - ALL US samples"
echo "Year: 2020"
echo "Running from: /fastscratch/tylerdoe"
echo "Branch: main (with enhanced report features)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2020

# Run pipeline for E. coli 2020 NARMS data
# Note: Set filter_state to null to process ALL states
# Uses main branch with enhanced report features (30+ metadata fields, QC tab improvements)
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state null \
    --filter_organism "Escherichia" \
    --filter_year_start 2020 \
    --filter_year_end 2020 \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir /fastscratch/tylerdoe/ecoli_2020_all_narms \
    -w work_ecoli_2020 \
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
    echo "Results location: /fastscratch/tylerdoe/ecoli_2020_all_narms"
    echo ""
    echo "Enhanced Summary Report:"
    echo "  - /fastscratch/tylerdoe/ecoli_2020_all_narms/summary/compass_summary.html"
    echo "  - /fastscratch/tylerdoe/ecoli_2020_all_narms/summary/compass_summary.tsv"
    echo ""
    echo "Report features:"
    echo "  • 30+ metadata fields (platform, model, bioproject, etc.)"
    echo "  • BUSCO quality metrics"
    echo "  • MLST typing data"
    echo "  • Enhanced QC tab"
    echo ""
    echo "Note: This includes ALL US E. coli 2020 NARMS samples"
    echo "Expected: ~500-1000 samples for 2020"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
