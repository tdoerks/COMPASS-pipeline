#!/bin/bash
#SBATCH --job-name=regen_2024_report
#SBATCH --output=/fastscratch/tylerdoe/regen_2024_report_%j.out
#SBATCH --error=/fastscratch/tylerdoe/regen_2024_report_%j.err
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Regenerating 2024 Report with Metadata Fix"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch COMPASS directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Pull latest fixes
git pull origin v1.1-stable

# Delete old COMBINE_RESULTS work to force regeneration
echo "Removing old COMBINE_RESULTS work directory..."
rm -rf work_2024/87/77056d*

# Load Nextflow
module load Nextflow

# Rerun with resume - will only regenerate COMBINE_RESULTS
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_kansas_2024 \
    -w work_2024 \
    -name kansas_2024_regen_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Report regenerated successfully!"
    echo ""
    echo "Report location: /fastscratch/tylerdoe/results_kansas_2024/summary/compass_report.html"
    echo ""
    echo "To download:"
    echo "scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/results_kansas_2024/summary/compass_report.html C:\\Users\\tdoerks\\Downloads\\compass_report_2024_fixed.html"
else
    echo "❌ Report generation failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
