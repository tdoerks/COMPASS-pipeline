#!/bin/bash
#SBATCH --job-name=ks_mo_ecoli_temporal
#SBATCH --output=/homes/tylerdoe/slurm-ks-mo-ecoli-temporal-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ks-mo-ecoli-temporal-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Kansas + Missouri E. coli Temporal Study"
echo "Jan 2021 - Jan 2026 (61 months)"
echo "100 samples per month = 6,100 total"
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

# Load Singularity/Apptainer (for running entrez-direct container)
module load Singularity 2>/dev/null || module load Apptainer 2>/dev/null || {
    echo "⚠️  WARNING: Could not load Singularity/Apptainer module"
    echo "   Trying to use singularity from PATH..."
}

# Use entrez-direct container (same as Nextflow pipeline)
ENTREZ_CONTAINER="docker://quay.io/biocontainers/entrez-direct:16.2--he881be0_1"

echo "Using entrez-direct container: $ENTREZ_CONTAINER"
echo ""

# Set unique Nextflow home to avoid cache conflicts
export NXF_HOME=/fastscratch/tylerdoe/.nextflow_ks_mo_temporal

# Set output directory
OUTPUT_DIR="/fastscratch/tylerdoe/ks_mo_ecoli_temporal_2021-2026_$(date +%Y%m%d)"
METADATA_DIR="${OUTPUT_DIR}/metadata"
mkdir -p "$METADATA_DIR"

echo "Working directory: $(pwd)"
echo "Output directory: $OUTPUT_DIR"
echo "Metadata directory: $METADATA_DIR"
echo ""

# ============================================================================
# STEP 1: Download E. coli metadata for 2021-2026
# ============================================================================

echo "=========================================="
echo "STEP 1: Downloading E. coli 2021-2026 metadata"
echo "=========================================="
echo ""

METADATA_FILE="${METADATA_DIR}/ecoli_2021-2026_all_metadata.csv"

echo "Querying NCBI SRA for E. coli samples from 2021-2026..."
echo "This may take several minutes for large datasets..."
echo ""

# Run entrez-direct in container
singularity exec "$ENTREZ_CONTAINER" bash -c \
    "esearch -db sra -query 'Escherichia coli[Organism] AND 2021:2026[Release Date]' | efetch -format runinfo" \
    > "$METADATA_FILE"

if [ ! -f "$METADATA_FILE" ] || [ ! -s "$METADATA_FILE" ]; then
    echo "❌ ERROR: Failed to download metadata"
    exit 1
fi

TOTAL_SAMPLES=$(tail -n +2 "$METADATA_FILE" | wc -l)
echo "✅ Downloaded metadata for $TOTAL_SAMPLES E. coli samples from 2021-2026"
echo ""

# ============================================================================
# STEP 2: Filter for Kansas + Missouri samples and stratify by month
# ============================================================================

echo "=========================================="
echo "STEP 2: Filter KS+MO & Temporal Stratification"
echo "=========================================="
echo ""

FILTERED_FILE="${METADATA_DIR}/ks_mo_temporal_filtered.csv"
SRR_LIST="${METADATA_DIR}/srr_accessions.txt"
SUMMARY_FILE="${METADATA_DIR}/sampling_summary.txt"

export OUTPUT_DIR_PY="$OUTPUT_DIR"

python3 << 'PYTHON_SCRIPT'
import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime

# Get output directory from environment
output_dir = os.environ['OUTPUT_DIR_PY']

# File paths
metadata_file = Path(f'{output_dir}/metadata/ecoli_2021-2026_all_metadata.csv')
output_file = Path(f'{output_dir}/metadata/ks_mo_temporal_filtered.csv')
srr_file = Path(f'{output_dir}/metadata/srr_accessions.txt')
summary_file = Path(f'{output_dir}/metadata/sampling_summary.txt')

print("=" * 60)
print("Reading E. coli metadata...")
print("=" * 60)
df = pd.read_csv(metadata_file)
print(f"Total E. coli samples (2021-2026): {len(df):,}")
print()

# ============================================================================
# Filter for Kansas + Missouri samples
# ============================================================================

print("=" * 60)
print("Filtering for Kansas + Missouri samples...")
print("=" * 60)

# Search for KS or MO patterns in sample-related columns
state_mask = pd.Series([False] * len(df))
sample_cols = [col for col in df.columns if any(x in col.lower() for x in ['sample', 'library', 'name', 'title'])]

print(f"Searching {len(sample_cols)} columns for state patterns:")
for col in sample_cols:
    print(f"  - {col}")

ks_pattern = r'(^|[^A-Z])KS($|[^A-Z])|kansas'
mo_pattern = r'(^|[^A-Z])MO($|[^A-Z])|missouri'

for col in sample_cols:
    if col in df.columns:
        # Kansas pattern
        ks_mask = df[col].astype(str).str.contains(ks_pattern, case=False, na=False, regex=True)
        # Missouri pattern
        mo_mask = df[col].astype(str).str.contains(mo_pattern, case=False, na=False, regex=True)
        state_mask |= (ks_mask | mo_mask)

df_states = df[state_mask].copy()
print(f"\nSamples with KS or MO pattern: {len(df_states):,}")

if len(df_states) == 0:
    print("\n❌ ERROR: No Kansas or Missouri samples found")
    print("   Check that sample naming includes state codes")
    sys.exit(1)

# Identify which state each sample belongs to
def identify_state(row):
    row_str = ' '.join([str(row[col]) for col in sample_cols if col in df.columns])
    if pd.isna(row_str):
        return 'Unknown'

    # Check for Kansas
    if pd.Series([row_str]).str.contains(ks_pattern, case=False, regex=True).iloc[0]:
        return 'Kansas'
    # Check for Missouri
    elif pd.Series([row_str]).str.contains(mo_pattern, case=False, regex=True).iloc[0]:
        return 'Missouri'
    else:
        return 'Unknown'

df_states['State'] = df_states.apply(identify_state, axis=1)

print("\nState distribution:")
state_counts = df_states['State'].value_counts()
for state, count in state_counts.items():
    print(f"  {state}: {count:,}")
print()

# ============================================================================
# Filter for Illumina + GENOMIC (isolates)
# ============================================================================

print("=" * 60)
print("Filtering for Illumina + GENOMIC samples...")
print("=" * 60)

if 'Platform' in df_states.columns:
    illumina_mask = df_states['Platform'].astype(str).str.upper() == 'ILLUMINA'
    df_states = df_states[illumina_mask]
    print(f"After Illumina filter: {len(df_states):,}")
else:
    print("⚠️  WARNING: 'Platform' column not found - skipping platform filter")

if 'LibrarySource' in df_states.columns:
    genomic_mask = df_states['LibrarySource'].astype(str).str.upper() == 'GENOMIC'
    df_states = df_states[genomic_mask]
    print(f"After GENOMIC filter: {len(df_states):,}")
else:
    print("⚠️  WARNING: 'LibrarySource' column not found - skipping library source filter")

if len(df_states) == 0:
    print("\n❌ ERROR: No samples passed filters")
    sys.exit(1)

print()

# ============================================================================
# Parse dates and create temporal groups
# ============================================================================

print("=" * 60)
print("Parsing release dates and creating temporal groups...")
print("=" * 60)

df_states['ReleaseDate'] = pd.to_datetime(df_states['ReleaseDate'], errors='coerce')
df_states = df_states[df_states['ReleaseDate'].notna()]
df_states['Year'] = df_states['ReleaseDate'].dt.year
df_states['Month'] = df_states['ReleaseDate'].dt.month
df_states['YearMonth'] = df_states['ReleaseDate'].dt.to_period('M')
df_states['MonthName'] = df_states['ReleaseDate'].dt.strftime('%B')

print(f"After date parsing: {len(df_states):,} samples")
print()

# Show distribution by year
print("Samples by year:")
year_counts = df_states['Year'].value_counts().sort_index()
for year, count in year_counts.items():
    print(f"  {year}: {count:,}")
print()

# ============================================================================
# Temporal stratification: 100 samples per month
# ============================================================================

print("=" * 60)
print("Temporal Stratification (100 samples per month)")
print("=" * 60)
print()

samples_per_month = 100
selected_samples = []

# Create date range: Jan 2021 through Jan 2026
start_date = pd.Period('2021-01', freq='M')
end_date = pd.Period('2026-01', freq='M')
all_months = pd.period_range(start=start_date, end=end_date, freq='M')

print(f"Target: {samples_per_month} samples per month")
print(f"Time range: {start_date} to {end_date} ({len(all_months)} months)")
print()

summary_lines = []
summary_lines.append("=" * 80)
summary_lines.append("Kansas + Missouri E. coli Temporal Sampling Summary")
summary_lines.append(f"Period: Jan 2021 - Jan 2026 ({len(all_months)} months)")
summary_lines.append(f"Target: {samples_per_month} samples per month")
summary_lines.append("=" * 80)
summary_lines.append("")

for year_month in all_months:
    month_df = df_states[df_states['YearMonth'] == year_month]

    year = year_month.year
    month = year_month.month

    if len(month_df) == 0:
        msg = f"  {year_month} ({year_month.strftime('%B %Y')}): ⚠️  NO SAMPLES AVAILABLE"
        print(msg)
        summary_lines.append(msg)
        continue

    # Count by state
    ks_count = len(month_df[month_df['State'] == 'Kansas'])
    mo_count = len(month_df[month_df['State'] == 'Missouri'])

    # Sample up to 100 (or all if less than 100)
    n_samples = min(samples_per_month, len(month_df))
    sampled = month_df.sample(n=n_samples, random_state=42)
    selected_samples.append(sampled)

    # Count selected by state
    ks_selected = len(sampled[sampled['State'] == 'Kansas'])
    mo_selected = len(sampled[sampled['State'] == 'Missouri'])

    msg = f"  {year_month} ({year_month.strftime('%B %Y')}): {n_samples:3d} selected (KS:{ks_selected}, MO:{mo_selected}) from {len(month_df):,} available (KS:{ks_count}, MO:{mo_count})"
    print(msg)
    summary_lines.append(msg)

print()
summary_lines.append("")

if not selected_samples:
    print("\n❌ ERROR: No samples selected")
    sys.exit(1)

# Combine all selected samples
final_df = pd.concat(selected_samples, ignore_index=True)
final_df = final_df.sort_values('ReleaseDate')

print("=" * 60)
print(f"✅ Final selection: {len(final_df):,} samples")
print("=" * 60)
print()

# Final distribution by year
print("Final distribution by year:")
for year in sorted(final_df['Year'].unique()):
    year_df = final_df[final_df['Year'] == year]
    ks_count = len(year_df[year_df['State'] == 'Kansas'])
    mo_count = len(year_df[year_df['State'] == 'Missouri'])
    print(f"  {year}: {len(year_df):,} (KS:{ks_count}, MO:{mo_count})")
print()

summary_lines.append("=" * 80)
summary_lines.append(f"TOTAL SAMPLES SELECTED: {len(final_df):,}")
summary_lines.append("")
summary_lines.append("Distribution by state:")
final_state_counts = final_df['State'].value_counts()
for state, count in final_state_counts.items():
    pct = (count / len(final_df)) * 100
    summary_lines.append(f"  {state}: {count:,} ({pct:.1f}%)")
summary_lines.append("")
summary_lines.append("Distribution by year:")
for year in sorted(final_df['Year'].unique()):
    year_df = final_df[final_df['Year'] == year]
    ks_count = len(year_df[year_df['State'] == 'Kansas'])
    mo_count = len(year_df[year_df['State'] == 'Missouri'])
    summary_lines.append(f"  {year}: {len(year_df):,} (KS:{ks_count}, MO:{mo_count})")
summary_lines.append("=" * 80)

# Save filtered metadata
final_df.to_csv(output_file, index=False)
print(f"✅ Saved filtered metadata: {output_file}")

# Save SRR accessions
with open(srr_file, 'w') as f:
    for srr in final_df['Run']:
        f.write(f"{srr}\n")
print(f"✅ Saved SRR list: {srr_file}")

# Save summary
with open(summary_file, 'w') as f:
    f.write('\n'.join(summary_lines))
print(f"✅ Saved sampling summary: {summary_file}")

print()
print("=" * 60)
print("Filtering and stratification complete!")
print("=" * 60)

PYTHON_SCRIPT

PYTHON_EXIT=$?

if [ $PYTHON_EXIT -ne 0 ]; then
    echo ""
    echo "❌ STEP 2 FAILED: Could not filter and stratify samples"
    exit 1
fi

# Count final samples
FINAL_COUNT=$(wc -l < "$SRR_LIST")
echo ""
echo "✅ STEP 2 COMPLETE"
echo "   Total samples selected: $FINAL_COUNT"
echo ""

# Display summary
if [ -f "$SUMMARY_FILE" ]; then
    echo "=========================================="
    echo "SAMPLING SUMMARY"
    echo "=========================================="
    cat "$SUMMARY_FILE"
    echo ""
fi

# ============================================================================
# STEP 3: Run COMPASS pipeline
# ============================================================================

echo "=========================================="
echo "STEP 3: Running COMPASS pipeline"
echo "=========================================="
echo ""
echo "This will process $FINAL_COUNT samples"
echo "Estimated runtime: 3-4 weeks"
echo ""
echo "Starting pipeline..."
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
    -w work_ks_mo_temporal \
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
    echo "Dataset: Kansas + Missouri E. coli Temporal Study"
    echo "  Total samples: $FINAL_COUNT"
    echo "  Period: Jan 2021 - Jan 2026 (61 months)"
    echo "  States: Kansas + Missouri"
    echo "  Platform: Illumina"
    echo "  Library source: GENOMIC (isolates)"
    echo ""
    echo "Metadata files:"
    echo "  - ${METADATA_DIR}/ecoli_2021-2026_all_metadata.csv (all E. coli)"
    echo "  - ${METADATA_DIR}/ks_mo_temporal_filtered.csv (filtered samples)"
    echo "  - ${METADATA_DIR}/srr_accessions.txt (SRR list)"
    echo "  - ${METADATA_DIR}/sampling_summary.txt (distribution report)"
    echo ""
else
    echo "❌ Pipeline failed with exit code $EXIT_CODE"
    echo "Check logs:"
    echo "  - /homes/tylerdoe/slurm-ks-mo-ecoli-temporal-${SLURM_JOB_ID}.out"
    echo "  - .nextflow.log"
    echo ""
    echo "To resume after fixing issues:"
    echo "  sbatch run_ks_mo_ecoli_temporal_2021-2026.sh"
fi

exit $EXIT_CODE
