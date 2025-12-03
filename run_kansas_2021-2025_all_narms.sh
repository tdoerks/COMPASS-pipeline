#!/bin/bash
#SBATCH --job-name=compass_ks_2021-2025
#SBATCH --output=/fastscratch/tylerdoe/slurm-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline v1.2-mod"
echo "Kansas NARMS 2021-2025 - ALL ORGANISMS"
echo "=========================================="
echo "Organisms: Campylobacter, Salmonella, E. coli"
echo "State: Kansas only"
echo "Years: 2021-2025"
echo "Running from: /fastscratch/tylerdoe"
echo ""
echo "BioProjects:"
echo "  - PRJNA292664 (Campylobacter)"
echo "  - PRJNA292661 (Salmonella)"
echo "  - PRJNA292663 (E. coli)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/compass-pipeline

# Load Nextflow
module load Nextflow

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ks_2021-2025

# Define output directory
OUTDIR="/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"

echo "Output directory: $OUTDIR"
echo ""

# Run pipeline for Kansas 2021-2025 NARMS data
# This uses the metadata_to_results workflow which:
#   1. Downloads metadata from all three NARMS BioProjects
#   2. Filters for Kansas samples (KS state code)
#   3. Filters for years 2021-2025
#   4. Downloads reads from SRA
#   5. Assembles genomes with SPAdes
#   6. Runs all analysis modules including MOB-suite
#   7. Generates comprehensive summary report

echo "Starting pipeline..."
echo "This will process all Kansas NARMS samples from 2021-2025"
echo "Expected sample count: ~150-300 samples (varies by year)"
echo ""

nextflow run main.nf \
    -profile beocat \
    --input_mode metadata \
    --bioproject "PRJNA292664,PRJNA292661,PRJNA292663" \
    --filter_state "KS" \
    --filter_year_start 2021 \
    --filter_year_end 2025 \
    --skip_busco true \
    --outdir $OUTDIR \
    -w work_ks_2021-2025 \
    -name kansas_2021-2025_${SLURM_JOB_ID} \
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
    echo "Results location: $OUTDIR"
    echo ""
    echo "Results breakdown by year:"
    echo "  You can find individual sample results in:"
    echo "  - $OUTDIR/mlst/"
    echo "  - $OUTDIR/amrfinderplus/"
    echo "  - $OUTDIR/mobsuite/"
    echo "  - $OUTDIR/prokka/"
    echo "  - etc."
    echo ""
    echo "Summary report (if COMPASS_SUMMARY module works):"
    echo "  - $OUTDIR/summary/compass_summary.tsv"
    echo "  - $OUTDIR/summary/compass_summary.html"
    echo ""
    echo "Sample filtering details:"
    echo "  - $OUTDIR/filtered_samples/"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Check sample counts:"
    echo "   ls $OUTDIR/mlst/*.tsv | wc -l"
    echo ""
    echo "2. Check which years are represented:"
    echo "   grep -h '^SRR' $OUTDIR/filtered_samples/*.txt | sort | head -20"
    echo ""
    echo "3. Copy results to homes for archiving (if satisfied):"
    echo "   cp -r $OUTDIR /homes/tylerdoe/pipelines/compass-pipeline/kansas_2021-2025_results_v1.2mod"
    echo ""
    echo "4. Generate summary report (if module failed):"
    echo "   ./bin/generate_compass_summary.py --outdir $OUTDIR --output_tsv summary.tsv --output_html summary.html"
    echo ""
    echo "5. Check for MOB-suite results:"
    echo "   ls -d $OUTDIR/mobsuite/*_mobsuite | wc -l"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Troubleshooting steps:"
    echo ""
    echo "1. Check SLURM output for errors:"
    echo "   tail -100 /fastscratch/tylerdoe/slurm-${SLURM_JOB_ID}.out"
    echo ""
    echo "2. Check Nextflow log:"
    echo "   tail -100 /fastscratch/tylerdoe/compass-pipeline/.nextflow.log"
    echo ""
    echo "3. Check failed processes:"
    echo "   grep 'ERROR' /fastscratch/tylerdoe/compass-pipeline/.nextflow.log"
    echo ""
    echo "4. Resume the pipeline after fixing issues:"
    echo "   sbatch run_kansas_2021-2025_all_narms.sh"
    echo "   (The -resume flag will skip completed work)"
    echo ""
fi

# Summary statistics
echo ""
echo "=========================================="
echo "QUICK STATS (if completed)"
echo "=========================================="

if [ -d "$OUTDIR" ]; then
    echo "Checking results..."

    # Count samples processed
    mlst_count=$(find $OUTDIR/mlst -name "*.tsv" 2>/dev/null | wc -l)
    amr_count=$(find $OUTDIR/amrfinderplus -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
    mob_count=$(find $OUTDIR/mobsuite -type d -name "*_mobsuite" 2>/dev/null | wc -l)

    echo "Samples with MLST results: $mlst_count"
    echo "Samples with AMR results: $amr_count"
    echo "Samples with MOB-suite results: $mob_count"

    if [ $mlst_count -gt 0 ]; then
        echo ""
        echo "✅ At least some results were generated!"

        if [ $mob_count -eq 0 ]; then
            echo "⚠️  WARNING: No MOB-suite results found!"
            echo "   Check if MOB-suite module ran successfully"
        elif [ $mob_count -lt $mlst_count ]; then
            echo "⚠️  WARNING: MOB-suite results incomplete ($mob_count vs $mlst_count)"
        else
            echo "✅ MOB-suite results look complete!"
        fi
    fi

    # Check for summary report
    if [ -f "$OUTDIR/summary/compass_summary.tsv" ]; then
        lines=$(wc -l < "$OUTDIR/summary/compass_summary.tsv")
        samples=$((lines - 1))
        echo ""
        echo "✅ Summary report exists with $samples samples"
    else
        echo ""
        echo "⚠️  Summary report not found (COMPASS_SUMMARY may have failed)"
    fi
else
    echo "No results directory found - pipeline may not have started"
fi

echo ""
echo "=========================================="
echo "Job complete!"
echo "=========================================="

exit $EXIT_CODE
