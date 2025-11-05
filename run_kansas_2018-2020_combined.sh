#!/bin/bash
#SBATCH --job-name=compass_ks_2018-2020
#SBATCH --output=/fastscratch/tylerdoe/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Kansas 2018-2020"
echo "Running all three years sequentially"
echo "Organisms: Campylobacter, Salmonella, E. coli"
echo "State: Kansas only"
echo "Running from: /fastscratch/tylerdoe"
echo "Branch: v1.2-dev"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Load Nextflow
module load Nextflow

# Track overall success
OVERALL_SUCCESS=0

# Run 2018
echo "=========================================="
echo "Starting 2018..."
echo "=========================================="
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_2018
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2018 \
    --filter_year_end 2018 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_kansas_2018 \
    -w work_2018 \
    -resume

if [ $? -eq 0 ]; then
    echo "✅ 2018 completed successfully!"
else
    echo "❌ 2018 failed!"
    OVERALL_SUCCESS=1
fi
echo ""

# Run 2019
echo "=========================================="
echo "Starting 2019..."
echo "=========================================="
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_2019
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2019 \
    --filter_year_end 2019 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_kansas_2019 \
    -w work_2019 \
    -resume

if [ $? -eq 0 ]; then
    echo "✅ 2019 completed successfully!"
else
    echo "❌ 2019 failed!"
    OVERALL_SUCCESS=1
fi
echo ""

# Run 2020
echo "=========================================="
echo "Starting 2020..."
echo "=========================================="
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_2020
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --filter_year_end 2020 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/results_kansas_2020 \
    -w work_2020 \
    -resume

if [ $? -eq 0 ]; then
    echo "✅ 2020 completed successfully!"
else
    echo "❌ 2020 failed!"
    OVERALL_SUCCESS=1
fi
echo ""

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "=========================================="

if [ $OVERALL_SUCCESS -eq 0 ]; then
    echo "✅ All years completed successfully!"
    echo ""
    echo "Results locations:"
    echo "  - /fastscratch/tylerdoe/results_kansas_2018"
    echo "  - /fastscratch/tylerdoe/results_kansas_2019"
    echo "  - /fastscratch/tylerdoe/results_kansas_2020"
else
    echo "❌ One or more years failed - check logs above"
fi

exit $OVERALL_SUCCESS
