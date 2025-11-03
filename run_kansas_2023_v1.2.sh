#!/bin/bash
#SBATCH --job-name=compass_ks_2023_v12
#SBATCH --output=/fastscratch/tylerdoe/ks_2023_v12_%j.out
#SBATCH --error=/fastscratch/tylerdoe/ks_2023_v12_%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline v1.2-dev - Kansas 2023"
echo "New Features: BUSCO, Enhanced Reports"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Ensure we're on v1.2-dev branch
echo "Switching to v1.2-dev branch..."
git fetch origin
git checkout v1.2-dev
git pull origin v1.2-dev

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_2023

# Run pipeline for Kansas 2023 NARMS data with v1.2 features
# - BUSCO enabled for assembly quality assessment
# - All organisms: Campylobacter, Salmonella, E. coli
# - Enhanced report with 6 visualizations
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --skip_busco false \
    --outdir /fastscratch/tylerdoe/results_kansas_2023_v1.2 \
    -w work_2023_v12 \
    -name kansas_2023_v12_${SLURM_JOB_ID} \
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
    echo "v1.2 Features Included:"
    echo "  - BUSCO assembly quality metrics"
    echo "  - Phage taxonomy labels (not contig IDs)"
    echo "  - 6 interactive visualizations"
    echo "  - Enhanced report navigation"
    echo ""
    echo "Results: /fastscratch/tylerdoe/results_kansas_2023_v1.2"
    echo ""
    echo "Generate enhanced report:"
    echo "  python bin/generate_report_v3.py \\"
    echo "    /fastscratch/tylerdoe/results_kansas_2023_v1.2 \\"
    echo "    -o /fastscratch/tylerdoe/results_kansas_2023_v1.2/summary/compass_report_enhanced.html \\"
    echo "    --prophage-metadata /homes/tylerdoe/databases/prophage_metadata.xlsx"
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /fastscratch/tylerdoe/ks_2023_v12_${SLURM_JOB_ID}.out"
fi

exit $EXIT_CODE
