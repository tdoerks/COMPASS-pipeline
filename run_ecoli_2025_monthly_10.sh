#!/bin/bash
#SBATCH --job-name=ecoli_2025_monthly
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-2025-monthly-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-2025-monthly-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "COMPASS Pipeline - E. coli 2025 Monthly Sampling"
echo "10 random samples per month from 2025"
echo "Total: 120 samples (12 months × 10 samples)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to fastscratch directory
cd /fastscratch/tylerdoe/COMPASS-pipeline || {
    echo "ERROR: Could not cd to /fastscratch/tylerdoe/COMPASS-pipeline"
    exit 1
}

# Load required modules
module load Nextflow || {
    echo "ERROR: Could not load Nextflow"
    exit 1
}

module load entrez-direct || {
    echo "ERROR: Could not load entrez-direct"
    exit 1
}

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ecoli_2025_monthly

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/ecoli_2025_monthly_$(date +%Y%m%d)"
METADATA_DIR="${OUTPUT_DIR}/metadata"
mkdir -p "$METADATA_DIR"

echo "Working directory: $(pwd)"
echo "Output directory: $OUTPUT_DIR"
echo "Metadata directory: $METADATA_DIR"
echo ""

# ============================================================================
# STEP 1: Download E. coli metadata for 2025
# ============================================================================

echo "=========================================="
echo "STEP 1: Downloading E. coli 2025 metadata"
echo "=========================================="
echo ""

METADATA_FILE="${METADATA_DIR}/ecoli_2025_metadata.csv"

echo "Querying NCBI SRA for E. coli samples from 2025..."
esearch -db sra -query "Escherichia coli[Organism] AND 2025[Release Date]" | \
    efetch -format runinfo > "$METADATA_FILE"

if [ ! -f "$METADATA_FILE" ] || [ ! -s "$METADATA_FILE" ]; then
    echo "❌ ERROR: Failed to download metadata"
    exit 1
fi

TOTAL_SAMPLES=$(tail -n +2 "$METADATA_FILE" | wc -l)
echo "✅ Downloaded metadata for $TOTAL_SAMPLES E. coli samples from 2025"
echo ""

# ============================================================================
# STEP 2: Filter and stratify by month (10 samples per month)
# ============================================================================

echo "=========================================="
echo "STEP 2: Stratified sampling by month"
echo "=========================================="
echo ""

FILTERED_FILE="${METADATA_DIR}/ecoli_2025_monthly_filtered.csv"
SRR_LIST="${METADATA_DIR}/srr_accessions.txt"

export OUTPUT_DIR_PY="$OUTPUT_DIR"

python3 << 'PYTHON_SCRIPT'
import pandas as pd
import sys
import os
from pathlib import Path

# Get output directory from environment
output_dir = os.environ['OUTPUT_DIR_PY']

# Read metadata
metadata_file = Path(f'{output_dir}/metadata/ecoli_2025_metadata.csv')
output_file = Path(f'{output_dir}/metadata/ecoli_2025_monthly_filtered.csv')
srr_file = Path(f'{output_dir}/metadata/srr_accessions.txt')

print("Reading metadata...")
df = pd.read_csv(metadata_file)
print(f"  Total samples: {len(df)}")

# Filter for Illumina + GENOMIC (isolates only)
if 'Platform' in df.columns:
    illumina_mask = df['Platform'].astype(str).str.upper() == 'ILLUMINA'
    df = df[illumina_mask]
    print(f"  After Illumina filter: {len(df)}")

if 'LibrarySource' in df.columns:
    genomic_mask = df['LibrarySource'].astype(str).str.upper() == 'GENOMIC'
    df = df[genomic_mask]
    print(f"  After GENOMIC filter: {len(df)}")

if len(df) == 0:
    print("\n❌ ERROR: No samples passed initial filters")
    sys.exit(1)

# Parse release date and extract month
df['ReleaseDate'] = pd.to_datetime(df['ReleaseDate'], errors='coerce')
df = df[df['ReleaseDate'].notna()]  # Remove samples with invalid dates
df['Month'] = df['ReleaseDate'].dt.month
df['MonthName'] = df['ReleaseDate'].dt.strftime('%B')

print(f"\nSamples by month (before sampling):")
month_counts = df.groupby('Month').size().sort_index()
for month, count in month_counts.items():
    month_name = df[df['Month'] == month]['MonthName'].iloc[0]
    print(f"  {month_name} ({month:02d}): {count}")

# Stratified sampling: 10 random samples per month
samples_per_month = 10
selected_samples = []

print(f"\nSelecting {samples_per_month} random samples per month...")
for month in range(1, 13):
    month_df = df[df['Month'] == month]

    if len(month_df) == 0:
        print(f"  ⚠️  Warning: No samples for month {month:02d}")
        continue

    # Sample up to 10 (or all if less than 10)
    n_samples = min(samples_per_month, len(month_df))
    sampled = month_df.sample(n=n_samples, random_state=42)
    selected_samples.append(sampled)

    month_name = sampled['MonthName'].iloc[0] if len(sampled) > 0 else f"Month {month}"
    print(f"  {month_name} ({month:02d}): {n_samples} samples (out of {len(month_df)} available)")

if not selected_samples:
    print("\n❌ ERROR: No samples selected")
    sys.exit(1)

# Combine all selected samples
final_df = pd.concat(selected_samples, ignore_index=True)
final_df = final_df.sort_values('ReleaseDate')

print(f"\n✅ Final selection: {len(final_df)} samples")
print(f"\nFinal distribution by month:")
for month in range(1, 13):
    count = len(final_df[final_df['Month'] == month])
    if count > 0:
        month_name = final_df[final_df['Month'] == month]['MonthName'].iloc[0]
        print(f"  {month_name} ({month:02d}): {count}")

# Save filtered metadata
final_df.to_csv(output_file, index=False)
print(f"\n✅ Saved filtered metadata: {output_file}")

# Save SRR accessions
with open(srr_file, 'w') as f:
    for srr in final_df['Run']:
        f.write(f"{srr}\n")
print(f"✅ Saved SRR list: {srr_file}")

PYTHON_SCRIPT

PYTHON_EXIT=$?

if [ $PYTHON_EXIT -ne 0 ]; then
    echo ""
    echo "❌ STEP 2 FAILED: Could not stratify samples"
    exit 1
fi

# Count final samples
FINAL_COUNT=$(wc -l < "$SRR_LIST")
echo ""
echo "✅ STEP 2 COMPLETE"
echo "   Total samples selected: $FINAL_COUNT"
echo ""

# ============================================================================
# STEP 3: Run COMPASS pipeline
# ============================================================================

echo "=========================================="
echo "STEP 3: Running COMPASS pipeline"
echo "=========================================="
echo ""

# Run pipeline using the filtered SRR list
nextflow run main.nf \
    -profile beocat \
    --input_mode accession \
    --accession_file "$SRR_LIST" \
    --skip_busco false \
    --busco_download_path /fastscratch/tylerdoe/databases/busco_downloads \
    --prophage_db /fastscratch/tylerdoe/databases/prophage_db.dmnd \
    --outdir "$OUTPUT_DIR" \
    -w work_ecoli_2025_monthly \
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
    echo "Summary Report:"
    echo "  - ${OUTPUT_DIR}/summary/compass_summary.html"
    echo "  - ${OUTPUT_DIR}/summary/compass_summary.tsv"
    echo ""
    echo "Dataset: E. coli 2025 Monthly Sampling"
    echo "  Total samples: $FINAL_COUNT (10 per month × 12 months)"
    echo "  Organism: Escherichia coli"
    echo "  Year: 2025"
    echo "  Platform: Illumina"
    echo "  Library source: GENOMIC (isolates)"
    echo ""
    echo "Metadata files:"
    echo "  - ${METADATA_DIR}/ecoli_2025_metadata.csv (all available)"
    echo "  - ${METADATA_DIR}/ecoli_2025_monthly_filtered.csv (selected)"
    echo "  - ${METADATA_DIR}/srr_accessions.txt (SRR list)"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs:"
    echo "  - /homes/tylerdoe/slurm-ecoli-2025-monthly-${SLURM_JOB_ID}.out"
    echo "  - .nextflow.log"
fi

exit $EXIT_CODE
