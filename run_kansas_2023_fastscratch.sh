#!/bin/bash
#SBATCH --job-name=compass_ks_2023
#SBATCH --output=/fastscratch/tylerdoe/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Kansas 2023"
echo "Organisms: Campylobacter, Salmonella, E. coli"
echo "State: Kansas only"
echo "Running from: /fastscratch/tylerdoe"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Run pipeline for Kansas 2023 NARMS data
# Automatically processes all three organisms:
#   - Campylobacter (PRJNA292664)
#   - Salmonella (PRJNA292661)
#   - E. coli (PRJNA292663)
# Filters for KS state code in sample names
# Uses separate work directory (work_2023) to avoid conflicts with other runs
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_kansas_2023 \
    -w work_2023 \
    -name kansas_2023 \
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
    echo "Results location: /fastscratch/tylerdoe/results_kansas_2023"
    echo ""
    echo "Next steps:"
    echo "1. Copy results to homes (if needed):"
    echo "   cp -r /fastscratch/tylerdoe/results_kansas_2023 /homes/tylerdoe/pipelines/compass-pipeline/"
    echo ""
    echo "2. Generate report:"
    echo "   ./bin/generate_report_v3.py /fastscratch/tylerdoe/results_kansas_2023 -o compass_report_ks_2023.html"
    echo ""
    echo "3. Download report:"
    echo "   scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/compass_report_ks_2023.html C:\\Users\\tdoerks\\Downloads\\"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
