#!/bin/bash
#SBATCH --job-name=bacteroides
#SBATCH --output=/fastscratch/tylerdoe/slurm-bacteroides-%j.out
#SBATCH --error=/fastscratch/tylerdoe/slurm-bacteroides-%j.err
#SBATCH --time=672:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - Bacteroides fragilis Study"
echo "=========================================="
echo "Organism: Bacteroides fragilis (obligate anaerobe)"
echo "Focus: Oxygen gradient study - anaerobe prophage burden"
echo "Hypothesis: Low prophage burden like Fusobacterium"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo "Node: $(hostname)"
echo ""

# Change to pipeline directory
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate"
PROJECT_DIR="$PIPELINE_DIR/bacteroides_fragilis_study"

cd "$PIPELINE_DIR" || {
    echo "ERROR: Could not cd to $PIPELINE_DIR"
    exit 1
}

# Load Nextflow
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

# Set unique Nextflow home
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_bacteroides

# Set Nextflow JVM heap size
export NXF_OPTS='-Xms2g -Xmx8g'

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/bacteroides_results"

echo "Working directory: $(pwd)"
echo "Project directory: $PROJECT_DIR"
echo "Input file: $PROJECT_DIR/data/samplesheet_bacteroides.txt"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if samplesheet exists
if [ ! -f "$PROJECT_DIR/data/samplesheet_bacteroides.txt" ]; then
    echo "ERROR: Samplesheet not found!"
    echo "Expected: $PROJECT_DIR/data/samplesheet_bacteroides.txt"
    echo ""
    echo "Please run the data download first:"
    echo "  1. cd $PROJECT_DIR"
    echo "  2. python3 scripts/fetch_bacteroides.py"
    echo "  3. python3 scripts/create_samplesheet.py"
    exit 1
fi

# Count samples
SAMPLE_COUNT=$(wc -l < "$PROJECT_DIR/data/samplesheet_bacteroides.txt")
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
    --input "$PROJECT_DIR/data/samplesheet_bacteroides.txt" \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "$OUTPUT_DIR" \
    -w work_bacteroides \
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
    echo "Key outputs for Bacteroides prophage analysis:"
    echo "  - MLST typing: $OUTPUT_DIR/mlst/"
    echo "  - Prophages (VIBRANT): $OUTPUT_DIR/vibrant/"
    echo "  - Plasmids (MOB-suite): $OUTPUT_DIR/mobsuite/"
    echo "  - AMR/Virulence (AMRFinder): $OUTPUT_DIR/amrfinder/"
    echo "  - ABRicate: $OUTPUT_DIR/abricate/"
    echo "  - BUSCO QC: $OUTPUT_DIR/busco/"
    echo "  - MultiQC report: $OUTPUT_DIR/multiqc/multiqc_report.html"
    echo "  - COMPASS summary: $OUTPUT_DIR/summary/"
    echo ""
    echo "Oxygen Gradient Analysis:"
    echo "  1. Extract prophage counts from VIBRANT integrated_prophage_coordinates"
    echo "  2. Compare to Fusobacterium (1.3 prophages/genome)"
    echo "  3. Compare to E. coli (8.2 prophages/genome - same niche, facultative)"
    echo "  4. Test hypothesis: anaerobes have lower prophage burden"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo ""
    echo "Check logs:"
    echo "  - SLURM output: /fastscratch/tylerdoe/slurm-bacteroides-${SLURM_JOB_ID}.out"
    echo "  - Nextflow log: $PIPELINE_DIR/.nextflow.log"
    echo ""
    echo "Resume with: sbatch $PROJECT_DIR/run_bacteroides.sh"
fi

exit $EXIT_CODE
