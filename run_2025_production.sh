#!/bin/bash
#SBATCH --job-name=compass_2025_prod
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - 2025 Production Run"
echo "Organisms: Campylobacter, Salmonella, E. coli"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

module load Nextflow

# Run pipeline for ALL 2025 NARMS data
# Automatically processes:
#   - Campylobacter (PRJNA292664)
#   - Salmonella (PRJNA292661)
#   - E. coli (PRJNA292663)
# No state filter = all states included
# Uses unique session name and work directory to avoid conflicts
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state null \
    --filter_year_start 2025 \
    --filter_year_end 2025 \
    --skip_busco true \
    --outdir results_2025_production \
    -w work_2025_prod \
    -name production_2025_${SLURM_JOB_ID} \
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
    echo "Next steps:"
    echo "1. Generate report:"
    echo "   ./bin/generate_report_v3.py results_2025_production -o compass_report_2025.html"
    echo ""
    echo "2. Download report:"
    echo "   scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/pipelines/compass-pipeline/compass_report_2025.html C:\\Users\\tdoerks\\Downloads\\"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: slurm-${SLURM_JOB_ID}.out and .nextflow.log"
fi

exit $EXIT_CODE
