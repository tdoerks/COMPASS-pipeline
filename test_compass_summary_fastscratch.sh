#!/bin/bash
#SBATCH --job-name=compass_summary_test
#SBATCH --output=/fastscratch/tylerdoe/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Summary Report Test"
echo "Testing new comprehensive summary module"
echo "Dataset: Kansas 2024 (small test dataset)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/compass-pipeline

# Load Nextflow
module load Nextflow

# Run pipeline for Kansas 2024 NARMS data (small dataset for testing)
# Test the new COMPASS_SUMMARY module which generates:
#   - compass_summary.tsv: Comprehensive tab-delimited table
#   - compass_summary.html: Interactive HTML report with sortable/filterable table
#
# Summary includes:
#   - Assembly quality metrics (QUAST)
#   - BUSCO completeness/contamination
#   - MLST sequence types
#   - SISTR serovars (Salmonella)
#   - AMR genes and MDR status
#   - Plasmid detection (MOB-suite)
#   - Prophage counts and classifications (VIBRANT + DIAMOND)

nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --bioproject "PRJNA292663" \
    --filter_state "KS" \
    --filter_year_start 2024 \
    --filter_year_end 2024 \
    --max_samples 20 \
    --outdir /fastscratch/tylerdoe/test_compass_summary \
    -w work_summary_test \
    -name summary_test_${SLURM_JOB_ID} \
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
    echo "Results location: /fastscratch/tylerdoe/test_compass_summary"
    echo ""
    echo "📊 Summary Report Outputs:"
    echo "   - TSV:  /fastscratch/tylerdoe/test_compass_summary/summary/compass_summary.tsv"
    echo "   - HTML: /fastscratch/tylerdoe/test_compass_summary/summary/compass_summary.html"
    echo ""
    echo "View summary table:"
    echo "   less /fastscratch/tylerdoe/test_compass_summary/summary/compass_summary.tsv"
    echo ""
    echo "Download HTML report:"
    echo "   scp tylerdoe@beocat.ksu.edu:/fastscratch/tylerdoe/test_compass_summary/summary/compass_summary.html ."
    echo ""
    echo "Summary includes:"
    echo "   ✓ Assembly quality (contigs, N50, length)"
    echo "   ✓ BUSCO completeness & contamination"
    echo "   ✓ MLST sequence types"
    echo "   ✓ AMR genes & MDR status"
    echo "   ✓ Plasmid detection"
    echo "   ✓ Prophage counts & classifications"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs:"
    echo "   - SLURM: /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out"
    echo "   - Nextflow: .nextflow.log"
    echo ""
    echo "Debug tips:"
    echo "   - Check module logs in work_summary_test/"
    echo "   - Verify compass_summary.nf module syntax"
    echo "   - Check generate_compass_summary.py script availability"
fi

exit $EXIT_CODE
