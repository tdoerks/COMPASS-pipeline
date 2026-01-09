#!/bin/bash
#SBATCH --job-name=compass_5sample_test
#SBATCH --output=/homes/tylerdoe/slurm-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-%j.err
#SBATCH --time=6:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - 5 Sample Test Run"
echo "Testing Enhanced Report Features"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""
echo "Test Configuration:"
echo "  • Samples: 5 (from Kansas 2021-2025)"
echo "  • Organisms: Mix of Salmonella, E. coli, Campylobacter"
echo "  • Goal: Validate enhanced HTML report"
echo "  • Features to test:"
echo "    - Metadata Explorer (49 SRA fields)"
echo "    - Quality Control tab (consolidated QC)"
echo "    - QC failures table"
echo "    - MultiQC link"
echo "=========================================="
echo ""

# Change to fastscratch directory for faster I/O
cd /fastscratch/tylerdoe/COMPASS-pipeline || {
    echo "ERROR: Could not cd to /fastscratch/tylerdoe/COMPASS-pipeline"
    echo "Please ensure pipeline is copied to fastscratch"
    exit 1
}

# Load Nextflow
module load Nextflow

# Set output directory
OUTDIR="/fastscratch/tylerdoe/test_5samples_v1.2mod"

echo "Pipeline directory: $(pwd)"
echo "Output directory: $OUTDIR"
echo ""

# Run pipeline with 5-sample limit
# Uses metadata filtering to automatically download and select samples
echo "Starting COMPASS pipeline..."
echo "Downloading metadata and selecting 5 diverse samples..."
echo ""

nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --filter_state "KS" \
    --filter_year_start 2021 \
    --filter_year_end 2025 \
    --max_samples 5 \
    --skip_busco false \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "$OUTDIR" \
    -w work_5sample_test \
    -name test_5samples_${SLURM_JOB_ID} \
    -resume

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Pipeline Execution Complete"
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Pipeline completed successfully!"
    echo ""
    echo "Results location: $OUTDIR"
    echo ""

    # Show what samples were processed
    echo "Samples processed:"
    if [ -f "$OUTDIR/filtered_samples/filtered_samples.csv" ]; then
        echo "----------------------------------------"
        head -6 "$OUTDIR/filtered_samples/filtered_samples.csv" | column -t -s,
        echo "----------------------------------------"
        SAMPLE_COUNT=$(tail -n +2 "$OUTDIR/filtered_samples/filtered_samples.csv" | wc -l)
        echo "Total: $SAMPLE_COUNT samples"
    fi
    echo ""

    echo "=========================================="
    echo "Generating Enhanced COMPASS Summary Report"
    echo "=========================================="
    echo ""

    # Step 1: Recreate filtered metadata from analyzed samples
    echo "Step 1: Recreating filtered metadata..."
    cd /fastscratch/tylerdoe/COMPASS-pipeline
    ./bin/recreate_filtered_metadata.py --outdir "$OUTDIR"

    if [ $? -ne 0 ]; then
        echo "⚠️  WARNING: Metadata recreation failed, but continuing..."
    fi

    echo ""
    echo "Step 2: Generating enhanced HTML report..."

    # Step 2: Generate comprehensive summary report
    ./bin/generate_compass_summary.py \
        --outdir "$OUTDIR" \
        --metadata "$OUTDIR/filtered_samples/filtered_samples.csv" \
        --output_tsv "$OUTDIR/compass_summary.tsv" \
        --output_html "$OUTDIR/compass_summary.html"

    REPORT_EXIT=$?

    echo ""
    echo "=========================================="
    echo "Test Run Complete!"
    echo "=========================================="

    if [ $REPORT_EXIT -eq 0 ]; then
        echo "✅ Enhanced report generated successfully!"
        echo ""
        echo "📊 Report Features to Validate:"
        echo "  1. Metadata Explorer tab"
        echo "     → Should show 40+ fields (not just 4)"
        echo "     → Fields: platform, model, librarystrategy, bioproject, etc."
        echo ""
        echo "  2. Quality Control tab"
        echo "     → N50, length, contigs, BUSCO histograms"
        echo "     → QC failures table (if any failed)"
        echo "     → Link to MultiQC report"
        echo ""
        echo "  3. All other tabs"
        echo "     → AMR Analysis, Plasmid Analysis, etc."
        echo "     → Verify data appears correctly"
        echo ""
        echo "📁 Output Files:"
        ls -lh "$OUTDIR/compass_summary.html" "$OUTDIR/compass_summary.tsv" 2>/dev/null || echo "  (files not found)"
        echo ""
        echo "🔍 To Download and Review:"
        echo "  scp tylerdoe@beocat.ksu.edu:$OUTDIR/compass_summary.html ."
        echo ""
        echo "  Open in web browser and verify:"
        echo "  - Metadata Explorer dropdown has 40+ fields"
        echo "  - Quality Control tab shows all QC metrics"
        echo "  - All tabs switch correctly"
        echo ""
    else
        echo "❌ Report generation failed with exit code $REPORT_EXIT"
        echo "Check error messages above"
    fi

    echo "=========================================="
    echo "Next Steps:"
    echo "=========================================="
    echo "1. Review the HTML report"
    echo "2. If report looks good:"
    echo "   → Integrate as automated final pipeline step"
    echo "   → Add Nextflow module for automatic report generation"
    echo "3. If issues found:"
    echo "   → Note specific problems"
    echo "   → Fix and re-run this test"
    echo ""
    echo "See SESSION_NOTES.md for detailed status and next steps"
    echo "=========================================="

else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Check logs for details:"
    echo "  SLURM output: /homes/tylerdoe/slurm-${SLURM_JOB_ID}.out"
    echo "  SLURM errors: /homes/tylerdoe/slurm-${SLURM_JOB_ID}.err"
    echo "  Nextflow log: .nextflow.log"
    echo ""
    echo "Common issues:"
    echo "  • Check database paths (prophage_db)"
    echo "  • Verify Nextflow module loaded correctly"
    echo "  • Check disk space on /fastscratch"
fi

echo ""
echo "End of test run"
exit $EXIT_CODE
