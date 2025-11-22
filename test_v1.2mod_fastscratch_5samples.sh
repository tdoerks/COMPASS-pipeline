#!/bin/bash
#SBATCH --job-name=compass_v12mod_test
#SBATCH --output=/fastscratch/tylerdoe/test_v12mod_%j.out
#SBATCH --error=/fastscratch/tylerdoe/test_v12mod_%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline v1.2-mod - TEST RUN"
echo "5 Sample Test on Fastscratch"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Fetch latest branches and checkout v1.2-mod
echo "Fetching branches from origin..."
git fetch origin

echo "Switching to v1.2-mod branch..."
git checkout v1.2-mod
git pull origin v1.2-mod

echo "Current branch: $(git branch --show-current)"
echo "Latest commit: $(git log -1 --oneline)"
echo ""

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_v12mod_test

# Run pipeline for Kansas 2023 - ONLY 5 SAMPLES for quick test
# Skip BUSCO to speed up test
nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2023 \
    --filter_year_end 2023 \
    --max_samples 5 \
    --skip_busco true \
    --outdir /fastscratch/tylerdoe/test_v1.2mod_5samples \
    -w /fastscratch/tylerdoe/work_v12mod_test \
    -name v12mod_test_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ v1.2-mod test run completed successfully!"
    echo ""
    echo "Results location: /fastscratch/tylerdoe/test_v1.2mod_5samples"
    echo ""
    echo "Check results:"
    echo "  ls -lh /fastscratch/tylerdoe/test_v1.2mod_5samples"
    echo ""
    echo "View summary report:"
    echo "  cat /fastscratch/tylerdoe/test_v1.2mod_5samples/summary/combined_summary.tsv | column -t -s $'\t'"
    echo ""
else
    echo "❌ Test run failed with exit code $EXIT_CODE"
    echo "Check logs:"
    echo "  tail -100 /fastscratch/tylerdoe/test_v12mod_${SLURM_JOB_ID}.out"
    echo "  tail -100 /fastscratch/tylerdoe/test_v12mod_${SLURM_JOB_ID}.err"
fi

exit $EXIT_CODE
