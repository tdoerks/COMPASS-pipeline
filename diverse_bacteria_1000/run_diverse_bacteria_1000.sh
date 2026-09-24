#!/bin/bash
#SBATCH --job-name=diverse_bacteria_1000
#SBATCH --output=/fastscratch/tylerdoe/slurm-diverse-bacteria-1000-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-diverse-bacteria-1000-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Diverse Bacteria 1000"
echo "=========================================="
echo "Dataset: 20 bacterial pathogens"
echo "Samples: 50 per organism = 1,000 total"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Node: $(hostname)"
echo ""

# Change to pipeline directory
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
PROJECT_DIR="$PIPELINE_DIR/diverse_bacteria_1000"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Load Nextflow
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_diverse_bacteria_1000

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/diverse_bacteria_1000_results"

echo "Working directory: $(pwd)"
echo "Project directory: $PROJECT_DIR"
echo "Input file: $PROJECT_DIR/samplesheet_diverse_1000.txt"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if samplesheet exists
if [ ! -f "$PROJECT_DIR/samplesheet_diverse_1000.txt" ]; then
    echo "ERROR: Samplesheet not found!"
    echo "Expected: $PROJECT_DIR/samplesheet_diverse_1000.txt"
    echo ""
    echo "Please run the data download first:"
    echo "  1. cd $PROJECT_DIR"
    echo "  2. python scripts/download_diverse_bacteria.py"
    echo "  3. python scripts/create_samplesheet.py"
    exit 1
fi

# Count samples
SAMPLE_COUNT=$(wc -l < "$PROJECT_DIR/samplesheet_diverse_1000.txt")
echo "Total samples in samplesheet: $SAMPLE_COUNT"
echo ""

# Run COMPASS pipeline
echo "=========================================="
echo "Starting COMPASS pipeline..."
echo "=========================================="
echo ""

nextflow run main.nf \
    -profile beocat \
    --input_mode sra_list \
    --input "$PROJECT_DIR/samplesheet_diverse_1000.txt" \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "$OUTPUT_DIR" \
    -w work_diverse_bacteria_1000 \
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
    echo "Results location: $OUTPUT_DIR"
    echo ""
    echo "Key outputs:"
    echo "  - MLST results: $OUTPUT_DIR/mlst/"
    echo "  - AMR results: $OUTPUT_DIR/amrfinder/"
    echo "  - ABRicate: $OUTPUT_DIR/abricate/"
    echo "  - Plasmids: $OUTPUT_DIR/mobsuite/"
    echo "  - BUSCO QC: $OUTPUT_DIR/busco/"
    echo "  - Prophages: $OUTPUT_DIR/vibrant/"
    echo "  - MultiQC: $OUTPUT_DIR/multiqc/multiqc_report.html"
    echo "  - Summary: $OUTPUT_DIR/summary/"
    echo ""
    echo "Quick stats:"
    mlst_count=$(find "$OUTPUT_DIR/mlst" -name "*.tsv" 2>/dev/null | wc -l)
    amr_count=$(find "$OUTPUT_DIR/amrfinder" -type d -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
    mob_count=$(find "$OUTPUT_DIR/mobsuite" -type d -name "*_mobsuite" 2>/dev/null | wc -l)
    echo "  Samples with MLST: $mlst_count"
    echo "  Samples with AMR: $amr_count"
    echo "  Samples with plasmids: $mob_count"
    echo ""
    echo "Analysis ideas:"
    echo "  1. Compare AMR profiles across 20 organisms"
    echo "  2. Plasmid diversity analysis"
    echo "  3. Prophage distribution by organism"
    echo "  4. MLST diversity assessment"
    echo "  5. Genome quality metrics (BUSCO) by organism"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Check logs:"
    echo "  - SLURM output: /fastscratch/tylerdoe/slurm-diverse-bacteria-1000-${SLURM_JOB_ID}.out"
    echo "  - Nextflow log: $PIPELINE_DIR/.nextflow.log"
    echo ""
    echo "Resume with: sbatch $PROJECT_DIR/run_diverse_bacteria_1000.sh"
fi

exit $EXIT_CODE
