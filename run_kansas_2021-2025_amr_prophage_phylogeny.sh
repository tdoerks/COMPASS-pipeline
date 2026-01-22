#!/bin/bash
#SBATCH --job-name=kansas_amr_prophage_phylo
#SBATCH --output=/homes/tylerdoe/slurm-kansas-amr-prophage-phylo-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-kansas-amr-prophage-phylo-%j.err
#SBATCH --time=96:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Kansas 2021-2025 AMR-Prophage Phylogeny"
echo "ONLY AMR-Carrying Prophages"
echo "Multi-Organism Dataset (Campy, Salmonella, E. coli)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_DIR="/homes/tylerdoe/kansas_2021-2025_amr_prophage_phylogeny_$(date +%Y%m%d)"

# AMR analysis result location (must run prophage-AMR analysis first!)
AMR_RESULTS_PATTERN="/homes/tylerdoe/kansas_2021-2025_prophage_amr_analysis_*/method3_direct_scan.csv"

# VIBRANT directory
VIBRANT_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod/vibrant"

# Create output directory
mkdir -p "$OUTPUT_DIR"
cd "$PIPELINE_DIR" || exit 1

echo "Pipeline directory: $PIPELINE_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if AMR analysis results exist
echo "Checking for AMR analysis results..."
AMR_CSV=$(ls -t $AMR_RESULTS_PATTERN 2>/dev/null | head -1)

if [ -z "$AMR_CSV" ]; then
    echo "❌ ERROR: AMR analysis results not found"
    echo "   Pattern searched: $AMR_RESULTS_PATTERN"
    echo ""
    echo "   You need to run the prophage-AMR analysis first:"
    echo "   sbatch run_kansas_2021-2025_prophage_amr_analysis.sh"
    echo ""
    exit 1
fi

echo "✓ AMR results found: $AMR_CSV"
echo ""

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
echo "AMR CSV: $AMR_CSV"
echo ""

export AMR_CSV_PY="$AMR_CSV"
export VIBRANT_DIR_PY="$VIBRANT_DIR"
export OUTPUT_FASTA_PY="$AMR_PROPHAGE_FASTA"
export OUTPUT_METADATA_PY="$AMR_PROPHAGE_METADATA"

python3 << 'PYTHON_SCRIPT'
import sys
import os
import csv
from pathlib import Path
from Bio import SeqIO

amr_csv = Path(os.environ['AMR_CSV_PY'])
vibrant_dir = Path(os.environ['VIBRANT_DIR_PY'])
output_fasta = Path(os.environ['OUTPUT_FASTA_PY'])
output_metadata = Path(os.environ['OUTPUT_METADATA_PY'])

# Parse AMR CSV to find samples with AMR in prophages
samples_with_amr = set()

print(f"Parsing AMR results from {amr_csv}...")
try:
    with open(amr_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip rows where gene is 'None' (samples with no AMR in prophages)
            if row.get('gene') != 'None' and row.get('gene'):
                if row.get('sample'):
                    samples_with_amr.add(row['sample'])
except Exception as e:
    print(f"❌ ERROR reading CSV: {e}")
    sys.exit(1)

print(f"  Found {len(samples_with_amr)} samples with AMR in prophages")

if not samples_with_amr:
    print("\n❌ ERROR: No AMR-carrying prophages found")
    print("   Check that the AMR analysis completed successfully")
    sys.exit(1)

# Extract prophage sequences for these samples
sequences = []
metadata_rows = []

print(f"\nExtracting prophages from {len(samples_with_amr)} samples...")

for i, sample_id in enumerate(sorted(samples_with_amr), 1):
    phage_file = vibrant_dir / f"{sample_id}_phages.fna"

    if not phage_file.exists():
        continue

    try:
        for record in SeqIO.parse(phage_file, "fasta"):
            orig_id = record.id
            record.id = f"kansas_{sample_id}_{orig_id}"
            record.description = f"sample={sample_id} amr=yes length={len(record.seq)}"

            sequences.append(record)

            metadata_rows.append({
                'prophage_id': record.id,
                'sample_id': sample_id,
                'amr_carrying': 'yes',
                'length_bp': len(record.seq),
                'original_id': orig_id
            })
    except Exception as e:
        print(f"  ⚠️  Error processing {sample_id}: {e}")

    if i % 50 == 0:
        print(f"  Processed {i}/{len(samples_with_amr)} samples...")

print(f"\n✅ Extracted {len(sequences)} AMR-carrying prophage sequences")

if not sequences:
    print("\n❌ ERROR: No prophage sequences extracted")
    sys.exit(1)

# Write FASTA
SeqIO.write(sequences, output_fasta, "fasta")
print(f"\n✅ Saved sequences to: {output_fasta}")

# Write metadata
with open(output_metadata, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['prophage_id', 'sample_id', 'amr_carrying', 'length_bp', 'original_id'], delimiter='\t')
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
    > "$ALIGNED_FASTA" 2> >(tee "$OUTPUT_DIR/mafft.log" >&2)

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
echo "   - amr_prophage_metadata.tsv (sample, AMR status)"
echo ""
echo "🔬 Key Questions to Explore:"
echo "   1. Do AMR-carrying prophages cluster by organism?"
echo "      (Campylobacter vs Salmonella vs E. coli)"
echo "   2. Are there Kansas-specific AMR prophage lineages?"
echo "   3. Do certain prophage clades carry more AMR genes?"
echo "   4. Is there evidence of horizontal AMR gene transfer via prophages?"
echo "      across different bacterial species?"
echo ""
echo "🌳 Next Steps:"
echo "   1. Download files and visualize in iTOL or FigTree"
echo "   2. Color tree by organism to see species-specific patterns"
echo "   3. Cross-reference with specific AMR genes carried"
echo "   4. Compare with all-prophage tree to identify AMR-specific lineages"
echo ""
echo "=========================================="

exit 0
