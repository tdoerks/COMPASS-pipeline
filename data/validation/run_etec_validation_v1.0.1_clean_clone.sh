#!/bin/bash
#SBATCH --job-name=etec_val_v1.0.1_clean
#SBATCH --output=/homes/tylerdoe/slurm-etec-validation-v1.0.1-clean-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-etec-validation-v1.0.1-clean-%j.err
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS v1.0.1 ETEC Validation (Clean Clone)"
echo "8 ETEC strains from doi:10.1038/s41598-021-88316-2"
echo "Testing: AMRFinder organism mapping + FASTA input summary fix"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
COMPASS_DIR="$( cd "$SCRIPT_DIR/../.." && pwd )"

# Change to COMPASS directory
cd "$COMPASS_DIR" || {
    echo "ERROR: Could not cd to $COMPASS_DIR"
    exit 1
}

# Verify we're on the correct branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "1.0.1-candidate-fasta-fix" ]; then
    echo "ERROR: Not on 1.0.1-candidate-fasta-fix branch (currently on: $CURRENT_BRANCH)"
    echo "Run: git checkout 1.0.1-candidate-fasta-fix"
    exit 1
fi

# Load Nextflow
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

# Set Nextflow JVM options
export NXF_OPTS='-Xms1g -Xmx4g'

echo "Working directory: $(pwd)"
echo "Pipeline branch: $CURRENT_BRANCH"
echo "Latest commit: $(git log --oneline -1)"
echo "Input file: data/validation/etec_samplesheet.csv"
echo "Output directory: data/validation/etec_results_v1.0.1_clean"
echo ""

# Verify input files exist
if [ ! -f "data/validation/etec_samplesheet.csv" ]; then
    echo "ERROR: Samplesheet not found: data/validation/etec_samplesheet.csv"
    exit 1
fi

if [ ! -d "data/validation/etec_genomes" ]; then
    echo "ERROR: ETEC genomes directory not found: data/validation/etec_genomes"
    exit 1
fi

echo "✅ Input validation passed"
echo ""

# Run COMPASS pipeline v1.0.1 (with FASTA input summary fix)
nextflow run main.nf \
    -profile beocat \
    --input data/validation/etec_samplesheet.csv \
    --outdir data/validation/etec_results_v1.0.1_clean \
    --input_mode fasta \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --prophage_metadata /fastscratch/tylerdoe/databases/prophage_metadata.xlsx \
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
    echo "Results: data/validation/etec_results_v1.0.1_clean"
    echo ""

    # Validation checks
    echo "Validation checks:"
    echo ""

    # Check AMR files
    AMR_COUNT=$(ls data/validation/etec_results_v1.0.1_clean/amrfinder/*_amr.tsv 2>/dev/null | wc -l)
    EMPTY_AMR=$(find data/validation/etec_results_v1.0.1_clean/amrfinder -name "*_amr.tsv" -size 0 2>/dev/null | wc -l)

    echo "  AMR files created: $AMR_COUNT / 8"
    echo "  Empty AMR files: $EMPTY_AMR"

    if [ $AMR_COUNT -eq 8 ] && [ $EMPTY_AMR -eq 0 ]; then
        echo "  ✅ All ETEC samples have non-empty AMR files"
    else
        echo "  ⚠️  Some AMR files missing or empty"
    fi

    # Check summary generation
    if [ -f "data/validation/etec_results_v1.0.1_clean/compass_summary.html" ]; then
        echo "  ✅ Summary HTML generated successfully"

        # Check for disclaimer
        if grep -q "disclaimer" data/validation/etec_results_v1.0.1_clean/compass_summary.html; then
            echo "  ✅ Disclaimer banner present in summary"
        else
            echo "  ⚠️  Disclaimer banner not found in summary"
        fi
    else
        echo "  ❌ Summary HTML not found"
    fi

    echo ""
    echo "Next steps:"
    echo "  1. Review summary report: data/validation/etec_results_v1.0.1_clean/compass_summary.html"
    echo "  2. Verify disclaimer banner appears"
    echo "  3. Check all analyses completed (AMR, prophages, plasmids, MLST, BUSCO, QUAST)"
    echo "  4. Compare with v1.1.0 results if needed"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs: /homes/tylerdoe/slurm-etec-validation-v1.0.1-clean-${SLURM_JOB_ID}.out"
    echo ""
    exit 1
fi

exit $EXIT_CODE
