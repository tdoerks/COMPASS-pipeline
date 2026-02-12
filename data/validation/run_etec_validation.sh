#!/bin/bash
#SBATCH --job-name=etec_validation
#SBATCH --output=/homes/tylerdoe/slurm-etec-validation-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-etec-validation-%j.err
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS ETEC Reference Genome Validation"
echo "8 ETEC strains from doi:10.1038/s41598-021-88316-2"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to COMPASS pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline || {
    echo "ERROR: Could not cd to /fastscratch/tylerdoe/COMPASS-pipeline"
    exit 1
}

# Load Nextflow
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

echo "Working directory: $(pwd)"
echo "Input file: data/validation/etec_samplesheet.csv"
echo "Output directory: data/validation/etec_results"
echo ""

# Run COMPASS pipeline
nextflow run main.nf \
    -profile beocat \
    --input data/validation/etec_samplesheet.csv \
    --outdir data/validation/etec_results \
    --input_mode fasta \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --max_cpus 8 \
    --max_memory 32.GB \
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
    echo "Results: data/validation/etec_results"
    echo ""
    echo "Next steps:"
    echo "  1. Review MultiQC report: data/validation/etec_results/multiqc/multiqc_report.html"
    echo "  2. Run validation analysis:"
    echo "     ./bin/validate_compass_results.py \\"
    echo "       data/validation/etec_results \\"
    echo "       data/validation/etec_ground_truth.csv \\"
    echo "       --output data/validation/etec_validation_report.md"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /homes/tylerdoe/slurm-etec-validation-${SLURM_JOB_ID}.out"
    echo ""
    exit 1
fi

exit $EXIT_CODE
