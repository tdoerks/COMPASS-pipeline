#!/bin/bash
#SBATCH --job-name=ecoli_amr_prophage_phylo
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-amr-prophage-phylo-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-amr-prophage-phylo-%j.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "E. coli AMR-Carrying Prophage Phylogeny"
echo "2021-2024 Dataset"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_DIR="/homes/tylerdoe/ecoli_amr_prophage_phylogeny_$(date +%Y%m%d)"

# AMR analysis results directories (from prophage-AMR analysis)
# These contain Method 3 results (direct AMRFinder scan - gold standard)
AMR_RESULTS_BASE="/homes/tylerdoe"

# Define AMR analysis result locations
declare -A AMR_RESULTS=(
    ["2021"]="$AMR_RESULTS_BASE/ecoli_2021_prophage_amr_analysis_*/method3_direct_scan.log"
    ["2022"]="$AMR_RESULTS_BASE/ecoli_prophage_amr_analysis_*/ecoli_2022/method3_direct_scan.log"
    ["2023"]="$AMR_RESULTS_BASE/ecoli_prophage_amr_analysis_*/ecoli_2023/method3_direct_scan.log"
    ["2024"]="$AMR_RESULTS_BASE/ecoli_prophage_amr_analysis_*/ecoli_2024/method3_direct_scan.log"
)

# Define E. coli VIBRANT output directories
declare -A VIBRANT_DIRS=(
    ["2021"]="/bulk/tylerdoe/archives/kansas_2021_ecoli/vibrant"
    ["2022"]="/bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant"
    ["2023"]="/bulk/tylerdoe/archives/results_ecoli_2023/vibrant"
    ["2024"]="/bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant"
)

# Create output directory
mkdir -p "$OUTPUT_DIR"
cd "$PIPELINE_DIR" || exit 1

echo "Pipeline directory: $PIPELINE_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if AMR analysis results exist
echo "Checking for AMR analysis results..."
MISSING_RESULTS=0
for year in 2021 2022 2023 2024; do
    pattern="${AMR_RESULTS[$year]}"
    files=$(ls $pattern 2>/dev/null | head -1)
    if [ -n "$files" ]; then
        echo "  ✓ $year: AMR results found"
    else
        echo "  ✗ $year: AMR results NOT found (need to run prophage-AMR analysis first)"
        MISSING_RESULTS=1
    fi
done
echo ""

if [ $MISSING_RESULTS -eq 1 ]; then
    echo "⚠️  WARNING: Some AMR analysis results are missing"
    echo "   This script requires completed AMR-prophage analysis"
    echo "   Run the prophage-AMR analysis scripts first:"
    echo "     - run_ecoli_2021_prophage_amr_analysis.sh"
    echo "     - run_ecoli_prophage_amr_analysis.sh (for 2022-2024)"
    echo ""
    echo "   Continuing with available data..."
    echo ""
fi

# Load required modules
echo "Loading required modules..."
module load MAFFT || echo "⚠️  MAFFT module not found"
module load Biopython/1.79-foss-2022a || echo "⚠️  Biopython module not found"
module load FastTree/2.1.11-GCCcore-11.3.0 || echo "⚠️  FastTree module not found"

# Verify Python can import Bio
echo ""
echo "Verifying BioPython installation..."
python3 -c "from Bio import SeqIO; print('✅ BioPython import successful')" || {
    echo "❌ ERROR: BioPython module loaded but Python cannot import it"
    exit 1
}

# Check if tools are available
echo ""
echo "Checking required tools..."
which mafft > /dev/null 2>&1 && echo "✅ MAFFT found" || echo "❌ MAFFT not found"
which FastTree > /dev/null 2>&1 && echo "✅ FastTree found" || echo "❌ FastTree not found"
echo ""

# ============================================================================
# STEP 1: Extract AMR-Carrying Prophage Sequences
# ============================================================================

echo "=========================================="
echo "STEP 1: Extract AMR-Carrying Prophages"
echo "=========================================="
echo ""

AMR_PROPHAGE_FASTA="$OUTPUT_DIR/amr_prophages.fasta"
AMR_PROPHAGE_METADATA="$OUTPUT_DIR/amr_prophage_metadata.tsv"

echo "Extracting only prophages that carry AMR genes..."
echo "Based on Method 3 (direct AMRFinder scan) results"
echo ""

# Export paths for Python
for year in 2021 2022 2023 2024; do
    export "AMR_RESULTS_${year}=${AMR_RESULTS[$year]}"
    export "VIBRANT_DIR_${year}=${VIBRANT_DIRS[$year]}"
done
export OUTPUT_FASTA_PY="$AMR_PROPHAGE_FASTA"
export OUTPUT_METADATA_PY="$AMR_PROPHAGE_METADATA"

python3 << 'PYTHON_SCRIPT'
import sys
import os
import re
from pathlib import Path
from Bio import SeqIO
import csv
from glob import glob

output_fasta = Path(os.environ['OUTPUT_FASTA_PY'])
output_metadata = Path(os.environ['OUTPUT_METADATA_PY'])

# Parse AMR analysis logs to find samples with AMR in prophages
amr_samples = {}  # year -> list of (sample_id, amr_genes)

for year in ['2021', '2022', '2023', '2024']:
    amr_pattern = os.environ.get(f'AMR_RESULTS_{year}')
    vibrant_dir = Path(os.environ.get(f'VIBRANT_DIR_{year}'))

    if not amr_pattern:
        continue

    # Find the actual log file
    log_files = glob(amr_pattern)
    if not log_files:
        print(f"⚠️  {year}: No AMR analysis log found")
        continue

    log_file = log_files[0]
    print(f"{year}: Parsing AMR results from {log_file}")

    # Parse log file to find samples with AMR genes in prophages
    # The log contains lines like: "SRR12345678: 3 AMR genes found in prophages"
    samples_with_amr = []
    try:
        with open(log_file, 'r') as f:
            for line in f:
                # Look for patterns indicating AMR genes found
                # Adjust regex based on actual output format
                if 'AMR gene' in line and 'prophage' in line:
                    # Try to extract sample ID
                    match = re.search(r'(SRR\d+|ERR\d+|DRR\d+)', line)
                    if match:
                        sample_id = match.group(1)
                        samples_with_amr.append(sample_id)
    except Exception as e:
        print(f"  ⚠️  Error parsing log: {e}")
        continue

    if samples_with_amr:
        amr_samples[year] = list(set(samples_with_amr))
        print(f"  Found {len(amr_samples[year])} samples with AMR in prophages")
    else:
        print(f"  ⚠️  No samples with AMR in prophages found")

# If no samples found from logs, try alternative: look for output CSV files
if not amr_samples:
    print("\n⚠️  No samples found from log parsing")
    print("   Trying to find CSV output files from Method 3...")

    for year in ['2021', '2022', '2023', '2024']:
        # Try to find the direct scan CSV
        csv_patterns = [
            f"/homes/tylerdoe/ecoli_{year}_prophage_amr_analysis_*/method3_direct_scan.csv",
            f"/homes/tylerdoe/ecoli_prophage_amr_analysis_*/ecoli_{year}/method3_direct_scan.csv"
        ]

        for pattern in csv_patterns:
            csv_files = glob(pattern)
            if csv_files:
                csv_file = csv_files[0]
                print(f"{year}: Found CSV: {csv_file}")
                try:
                    with open(csv_file, 'r') as f:
                        reader = csv.DictReader(f)
                        samples = set()
                        for row in reader:
                            # CSV should have sample_id and prophage info
                            if row.get('sample_id'):
                                samples.add(row['sample_id'])
                    if samples:
                        amr_samples[year] = list(samples)
                        print(f"  Found {len(samples)} samples with AMR prophages")
                except Exception as e:
                    print(f"  ⚠️  Error reading CSV: {e}")
                break

if not amr_samples:
    print("\n❌ ERROR: Could not find any AMR-carrying prophages")
    print("   Please ensure AMR prophage analysis has been run:")
    print("     - run_ecoli_2021_prophage_amr_analysis.sh")
    print("     - run_ecoli_prophage_amr_analysis.sh")
    sys.exit(1)

# Now extract prophage sequences for these samples
sequences = []
metadata_rows = []

for year, sample_list in sorted(amr_samples.items()):
    vibrant_dir = Path(os.environ.get(f'VIBRANT_DIR_{year}'))

    if not vibrant_dir.exists():
        print(f"⚠️  {year}: VIBRANT directory not found: {vibrant_dir}")
        continue

    print(f"\n{year}: Extracting prophages from {len(sample_list)} samples...")

    for sample_id in sample_list:
        phage_file = vibrant_dir / f"{sample_id}_phages.fna"

        if not phage_file.exists():
            continue

        try:
            for record in SeqIO.parse(phage_file, "fasta"):
                orig_id = record.id
                record.id = f"{year}_{sample_id}_{orig_id}"
                record.description = f"year={year} sample={sample_id} amr=yes length={len(record.seq)}"

                sequences.append(record)

                metadata_rows.append({
                    'prophage_id': record.id,
                    'year': year,
                    'sample_id': sample_id,
                    'amr_carrying': 'yes',
                    'length_bp': len(record.seq),
                    'original_id': orig_id
                })
        except Exception as e:
            print(f"  ⚠️  Error processing {sample_id}: {e}")

print(f"\n✅ Extracted {len(sequences)} AMR-carrying prophage sequences")
print(f"   Breakdown by year:")
from collections import Counter
year_counts = Counter(m['year'] for m in metadata_rows)
for year in sorted(year_counts.keys()):
    print(f"     {year}: {year_counts[year]} prophages")

if not sequences:
    print("\n❌ ERROR: No prophage sequences extracted")
    sys.exit(1)

# Write FASTA
SeqIO.write(sequences, output_fasta, "fasta")
print(f"\n✅ Saved sequences to: {output_fasta}")

# Write metadata
with open(output_metadata, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['prophage_id', 'year', 'sample_id', 'amr_carrying', 'length_bp', 'original_id'], delimiter='\t')
    writer.writeheader()
    writer.writerows(metadata_rows)

print(f"✅ Saved metadata to: {output_metadata}")
print(f"\nTotal sequences: {len(sequences)}")
print(f"Total size: {sum(len(s.seq) for s in sequences):,} bp")

PYTHON_SCRIPT

STEP1_EXIT=$?

if [ $STEP1_EXIT -ne 0 ]; then
    echo ""
    echo "❌ STEP 1 FAILED: Could not extract AMR-carrying prophages"
    exit 1
fi

if [ ! -f "$AMR_PROPHAGE_FASTA" ]; then
    echo "❌ ERROR: Prophage FASTA file not created"
    exit 1
fi

NUM_SEQS=$(grep -c "^>" "$AMR_PROPHAGE_FASTA")

echo ""
echo "✅ STEP 1 COMPLETE"
echo "   Sequences: $NUM_SEQS AMR-carrying prophages"
echo ""

# ============================================================================
# STEP 2: Multiple Sequence Alignment with MAFFT
# ============================================================================

echo "=========================================="
echo "STEP 2: Multiple Sequence Alignment"
echo "=========================================="
echo ""

ALIGNED_FASTA="$OUTPUT_DIR/amr_prophages_aligned.fasta"

if ! which mafft > /dev/null 2>&1; then
    echo "❌ ERROR: MAFFT not found"
    exit 1
fi

echo "Running MAFFT alignment on $NUM_SEQS AMR-carrying prophages..."
echo "Output: $ALIGNED_FASTA"
echo ""

START_TIME=$(date +%s)

mafft \
    --auto \
    --thread $SLURM_CPUS_PER_TASK \
    "$AMR_PROPHAGE_FASTA" \
    > "$ALIGNED_FASTA" 2>&1 | tee "$OUTPUT_DIR/mafft.log"

MAFFT_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))

echo ""
if [ $MAFFT_EXIT -eq 0 ] && [ -s "$ALIGNED_FASTA" ]; then
    echo "✅ MAFFT alignment completed in ${MINUTES} minutes"
else
    echo "❌ MAFFT alignment failed"
    exit 1
fi

echo ""

# ============================================================================
# STEP 3: Phylogenetic Tree Construction with FastTree
# ============================================================================

echo "=========================================="
echo "STEP 3: Phylogenetic Tree Construction"
echo "=========================================="
echo ""

TREE_FILE="$OUTPUT_DIR/amr_prophage_tree.nwk"

if ! which FastTree > /dev/null 2>&1; then
    echo "❌ ERROR: FastTree not found"
    exit 1
fi

echo "Running FastTree on AMR-carrying prophages..."
echo "Output: $TREE_FILE"
echo ""

START_TIME=$(date +%s)

FastTree -nt -gtr -gamma -boot 1000 "$ALIGNED_FASTA" > "$TREE_FILE" 2>&1

FASTTREE_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))

echo ""
if [ $FASTTREE_EXIT -eq 0 ] && [ -s "$TREE_FILE" ]; then
    echo "✅ FastTree completed in ${MINUTES} minutes"
else
    echo "❌ FastTree failed"
    exit 1
fi

echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo "=========================================="
echo "🎉 AMR-PROPHAGE PHYLOGENY COMPLETE!"
echo "=========================================="
echo ""
echo "End time: $(date)"
echo ""
echo "📁 Output Directory: $OUTPUT_DIR"
echo ""
echo "📊 Output Files:"
echo "   - amr_prophage_tree.nwk (phylogenetic tree)"
echo "   - amr_prophages.fasta (AMR-carrying prophage sequences)"
echo "   - amr_prophages_aligned.fasta (alignment)"
echo "   - amr_prophage_metadata.tsv (year, sample, AMR status)"
echo ""
echo "🔬 Key Questions to Explore:"
echo "   1. Do AMR-carrying prophages cluster together?"
echo "   2. Are there year-specific AMR prophage lineages?"
echo "   3. Do certain prophage clades carry more AMR genes?"
echo "   4. Is there evidence of horizontal AMR gene transfer via prophages?"
echo ""
echo "🌳 Next Steps:"
echo "   1. Download files and visualize in iTOL or FigTree"
echo "   2. Color tree by year (2021-2024)"
echo "   3. Cross-reference with specific AMR genes carried"
echo "   4. Compare with all-prophage tree to identify AMR-specific lineages"
echo ""
echo "=========================================="

exit 0
