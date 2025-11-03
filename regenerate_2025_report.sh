#!/bin/bash
#SBATCH --job-name=regen_2025_report
#SBATCH --output=regen_2025_report_%j.out
#SBATCH --error=regen_2025_report_%j.err
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Regenerating 2025 Report with Metadata"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Load Nextflow
module load Nextflow

# Run pipeline with resume - will only regenerate COMBINE_RESULTS
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2025 \
    --filter_year_end 2025 \
    --skip_busco true \
    --outdir results_kansas_2025 \
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
    echo "Report location: results_kansas_2025/summary/compass_report.html"
    echo ""
    echo "To download:"
    echo "scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/pipelines/compass-pipeline/results_kansas_2025/summary/compass_report.html C:\\Users\\tdoerks\\Downloads\\"
else
    echo "❌ Report generation failed with exit code $EXIT_CODE"
fi

exit $EXIT_CODE
