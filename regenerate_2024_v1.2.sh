#!/bin/bash
#SBATCH --job-name=regen_2024_v1.2
#SBATCH --output=/fastscratch/tylerdoe/regen_2024_v1.2_%j.out
#SBATCH --error=/fastscratch/tylerdoe/regen_2024_v1.2_%j.err
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Regenerating 2024 Report - v1.2-dev"
echo "With: BUSCO + Phage Taxonomy"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch COMPASS directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Switch to v1.2-dev and pull latest
echo "Switching to v1.2-dev branch..."
git fetch origin
git checkout v1.2-dev
git pull origin v1.2-dev

# Delete old COMBINE_RESULTS work to force report regeneration
echo "Removing old COMBINE_RESULTS work directory..."
find work_2024 -type d -name "COMBINE_RESULTS" -exec rm -rf {} + 2>/dev/null || true

# Load Nextflow
module load Nextflow

# Rerun with resume - will regenerate report AND run BUSCO on existing assemblies
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --skip_busco false \
    --outdir /fastscratch/tylerdoe/results_kansas_2024 \
    -w work_2024 \
    -name kansas_2024_v12_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ v1.2 Report regenerated successfully!"
    echo ""
    echo "New features:"
    echo "  - BUSCO quality metrics for all 167 samples"
    echo "  - Phage taxonomy labels (not contig IDs)"
    echo ""
    echo "Report location: /fastscratch/tylerdoe/results_kansas_2024/summary/compass_report.html"
    echo ""
    echo "To download:"
    echo "scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/results_kansas_2024/summary/compass_report.html C:\\Users\\tdoerks\\Downloads\\compass_report_2024_v1.2.html"
else
    echo "❌ Report generation failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
