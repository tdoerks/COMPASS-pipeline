#!/bin/bash
#SBATCH --job-name=ecoli_monthly_100
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-monthly-100-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-monthly-100-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - E. coli Monthly 100"
echo "100 samples per month: Jan 2020 - Jan 2026"
echo "Total: 7,142 samples"
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
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_monthly_100

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_monthly_100_$(date +%Y%m%d)"

echo "Working directory: $(pwd)"
echo "Input file: sra_accessions_ecoli_monthly_100_2020-2026.txt"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Run COMPASS pipeline
nextflow run main.nf \
    -profile beocat \
    --input_mode sra_list \
    --input sra_accessions_ecoli_monthly_100_2020-2026.txt \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "$OUTPUT_DIR" \
    -w work_ecoli_monthly_100 \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Pipeline completed successfully!"
    echo "Results: $OUTPUT_DIR"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /homes/tylerdoe/slurm-ecoli-monthly-100-${SLURM_JOB_ID}.out"
fi

exit $EXIT_CODE
