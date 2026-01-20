#!/bin/bash
#SBATCH --job-name=ecoli_all_prophage_phylo
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-all-prophage-phylo-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-all-prophage-phylo-%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Complete E. coli Prophage Phylogenetic Analysis"
echo "2021-2024 Multi-Year Dataset"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
OUTPUT_DIR="/homes/tylerdoe/ecoli_all_prophage_phylogeny_$(date +%Y%m%d)"

# Define all E. coli datasets
declare -A DATASETS=(
    ["2021"]="/bulk/tylerdoe/archives/kansas_2021_ecoli"
    ["2022"]="/bulk/tylerdoe/archives/kansas_2022_ecoli"
    ["2023"]="/bulk/tylerdoe/archives/results_ecoli_2023"
    ["2024"]="/bulk/tylerdoe/archives/results_ecoli_all_2024"
)

# Create output directory
mkdir -p "$OUTPUT_DIR"
cd "$PIPELINE_DIR" || exit 1

echo "Pipeline directory: $PIPELINE_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Datasets to analyze:"
for year in 2021 2022 2023 2024; do
    dir="${DATASETS[$year]}"
    if [ -d "$dir" ]; then
        count=$(find "$dir/vibrant" -name "*_phages.fna" 2>/dev/null | wc -l)
        echo "  ✓ E. coli $year: $count samples with prophages"
    else
        echo "  ✗ E. coli $year: Directory not found"
    fi
done
echo ""

# Load required modules
echo "Loading required modules..."
module load MAFFT || echo "⚠️  MAFFT module not found, trying system install"
module load Biopython/1.79-foss-2022a || echo "⚠️  Biopython module not found"
module load FastTree/2.1.11-GCCcore-11.3.0 || echo "⚠️  FastTree module not found"

# Verify Python can import Bio
echo ""
echo "Verifying BioPython installation..."
python3 -c "from Bio import SeqIO; print('✅ BioPython import successful')" || {
    echo "❌ ERROR: BioPython module loaded but Python cannot import it"
    echo "   This may be a PYTHONPATH issue"
    exit 1
}

# Check if tools are available
echo ""
echo "Checking required tools..."
which mafft > /dev/null 2>&1 && echo "✅ MAFFT found: $(which mafft)" || echo "❌ MAFFT not found"
which FastTree > /dev/null 2>&1 && echo "✅ FastTree found: $(which FastTree)" || echo "❌ FastTree not found"
which python3 > /dev/null 2>&1 && echo "✅ Python3 found: $(which python3)" || echo "❌ Python3 not found"
echo ""

# ============================================================================
# STEP 1: Extract Prophage Sequences from All Datasets
# ============================================================================

echo "=========================================="
echo "STEP 1: Extracting Prophage Sequences"
echo "=========================================="
echo ""

PROPHAGE_FASTA="$OUTPUT_DIR/prophages_all.fasta"
PROPHAGE_METADATA="$OUTPUT_DIR/prophage_metadata.tsv"

echo "Extracting prophage sequences from VIBRANT output..."
echo "This will combine prophages from all 4 years (2021-2024)..."
echo ""

# Create Python script to extract from multiple datasets
export OUTPUT_FASTA_PY="$PROPHAGE_FASTA"
export OUTPUT_METADATA_PY="$PROPHAGE_METADATA"
export DATASET_2021="${DATASETS[2021]}"
export DATASET_2022="${DATASETS[2022]}"
export DATASET_2023="${DATASETS[2023]}"
export DATASET_2024="${DATASETS[2024]}"

python3 << 'PYTHON_SCRIPT'
import sys
import os
from pathlib import Path
from Bio import SeqIO
import csv

output_fasta = Path(os.environ['OUTPUT_FASTA_PY'])
output_metadata = Path(os.environ['OUTPUT_METADATA_PY'])

datasets = {
    '2021': Path(os.environ['DATASET_2021']),
    '2022': Path(os.environ['DATASET_2022']),
    '2023': Path(os.environ['DATASET_2023']),
    '2024': Path(os.environ['DATASET_2024'])
}

sequences = []
metadata_rows = []

for year, results_dir in sorted(datasets.items()):
    vibrant_dir = results_dir / "vibrant"

    if not vibrant_dir.exists():
        print(f"⚠️  {year}: VIBRANT directory not found: {vibrant_dir}")
        continue

    phage_files = list(vibrant_dir.glob("*_phages.fna"))
    print(f"\n{year}: Found {len(phage_files)} samples with prophage data")

    for i, phage_file in enumerate(sorted(phage_files), 1):
        sample_id = phage_file.stem.replace('_phages', '')

        if i % 100 == 0:
            print(f"  Processed {i}/{len(phage_files)} samples...")

        try:
            for record in SeqIO.parse(phage_file, "fasta"):
                # Rename sequence ID to include year and sample
                orig_id = record.id
                record.id = f"{year}_{sample_id}_{orig_id}"
                record.description = f"year={year} sample={sample_id} length={len(record.seq)}"

                sequences.append(record)

                # Store metadata
                metadata_rows.append({
                    'prophage_id': record.id,
                    'year': year,
                    'sample_id': sample_id,
                    'length_bp': len(record.seq),
                    'original_id': orig_id
                })
        except Exception as e:
            print(f"  ⚠️  Error processing {phage_file.name}: {e}")

print(f"\n✅ Extracted {len(sequences)} total prophage sequences from all years")
print(f"   Breakdown by year:")
from collections import Counter
year_counts = Counter(m['year'] for m in metadata_rows)
for year in sorted(year_counts.keys()):
    print(f"     {year}: {year_counts[year]} prophages")

# Write FASTA
SeqIO.write(sequences, output_fasta, "fasta")
print(f"\n✅ Saved sequences to: {output_fasta}")

# Write metadata
with open(output_metadata, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['prophage_id', 'year', 'sample_id', 'length_bp', 'original_id'], delimiter='\t')
    writer.writeheader()
    writer.writerows(metadata_rows)

print(f"✅ Saved metadata to: {output_metadata}")
print(f"\nTotal sequences: {len(sequences)}")
print(f"Total size: {sum(len(s.seq) for s in sequences):,} bp")

# Calculate size statistics
lengths = [len(s.seq) for s in sequences]
if lengths:
    import statistics
    print(f"Length range: {min(lengths):,} - {max(lengths):,} bp")
    print(f"Mean length: {statistics.mean(lengths):,.0f} bp")
    print(f"Median length: {statistics.median(lengths):,.0f} bp")

PYTHON_SCRIPT

STEP1_EXIT=$?

if [ $STEP1_EXIT -ne 0 ]; then
    echo ""
    echo "❌ STEP 1 FAILED: Could not extract prophage sequences"
    echo "Check error messages above"
    exit 1
fi

if [ ! -f "$PROPHAGE_FASTA" ]; then
    echo "❌ ERROR: Prophage FASTA file not created"
    exit 1
fi

NUM_SEQS=$(grep -c "^>" "$PROPHAGE_FASTA")
TOTAL_SIZE=$(stat -c%s "$PROPHAGE_FASTA" 2>/dev/null || stat -f%z "$PROPHAGE_FASTA")

echo ""
echo "✅ STEP 1 COMPLETE"
echo "   Sequences: $NUM_SEQS"
echo "   FASTA size: $((TOTAL_SIZE / 1024 / 1024)) MB"
echo ""

# ============================================================================
# STEP 2: Subsample if Too Many Sequences
# ============================================================================

echo "=========================================="
echo "STEP 2: Subsample (if needed)"
echo "=========================================="
echo ""

MAX_SEQS=500  # Maximum sequences for reasonable phylogeny runtime

if [ "$NUM_SEQS" -gt "$MAX_SEQS" ]; then
    echo "⚠️  Dataset has $NUM_SEQS sequences (> $MAX_SEQS)"
    echo "   Subsampling to $MAX_SEQS sequences for manageable runtime..."
    echo ""

    SUBSAMPLED_FASTA="$OUTPUT_DIR/prophages_subsampled.fasta"

    # Python-based subsampling
    python3 << PYCODE
from Bio import SeqIO
import random

random.seed(42)
records = list(SeqIO.parse("$PROPHAGE_FASTA", "fasta"))
sampled = random.sample(records, min($MAX_SEQS, len(records)))
SeqIO.write(sampled, "$SUBSAMPLED_FASTA", "fasta")
print(f"✅ Subsampled {len(sampled)} sequences")
PYCODE

    ALIGNMENT_INPUT="$SUBSAMPLED_FASTA"
    NUM_SEQS=$MAX_SEQS
    echo "   Using subsampled FASTA for alignment: $ALIGNMENT_INPUT"
else
    echo "✅ Dataset size OK ($NUM_SEQS sequences ≤ $MAX_SEQS)"
    echo "   Using full dataset for alignment"
    ALIGNMENT_INPUT="$PROPHAGE_FASTA"
fi

echo ""

# ============================================================================
# STEP 3: Multiple Sequence Alignment with MAFFT
# ============================================================================

echo "=========================================="
echo "STEP 3: Multiple Sequence Alignment"
echo "=========================================="
echo ""

ALIGNED_FASTA="$OUTPUT_DIR/prophages_aligned.fasta"

if ! which mafft > /dev/null 2>&1; then
    echo "❌ ERROR: MAFFT not found"
    echo "   Cannot perform alignment without MAFFT"
    exit 1
fi

echo "Running MAFFT alignment..."
echo "Input: $ALIGNMENT_INPUT ($NUM_SEQS sequences)"
echo "Output: $ALIGNED_FASTA"
echo ""
echo "This may take 30-60 minutes depending on dataset size..."
echo ""

START_TIME=$(date +%s)

mafft \
    --auto \
    --thread $SLURM_CPUS_PER_TASK \
    "$ALIGNMENT_INPUT" \
    > "$ALIGNED_FASTA" 2> >(tee "$OUTPUT_DIR/mafft.log" >&2)

MAFFT_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))

echo ""
if [ $MAFFT_EXIT -eq 0 ] && [ -s "$ALIGNED_FASTA" ]; then
    echo "✅ MAFFT alignment completed in ${MINUTES} minutes"
    ALIGNED_SIZE=$(stat -c%s "$ALIGNED_FASTA" 2>/dev/null || stat -f%z "$ALIGNED_FASTA")
    echo "   Aligned FASTA size: $((ALIGNED_SIZE / 1024 / 1024)) MB"
else
    echo "❌ MAFFT alignment failed"
    echo "Check log: $OUTPUT_DIR/mafft.log"
    exit 1
fi

echo ""

# ============================================================================
# STEP 4: Phylogenetic Tree Construction with FastTree
# ============================================================================

echo "=========================================="
echo "STEP 4: Phylogenetic Tree Construction"
echo "=========================================="
echo ""

TREE_FILE="$OUTPUT_DIR/prophage_tree.nwk"

if ! which FastTree > /dev/null 2>&1; then
    echo "❌ ERROR: FastTree not found"
    echo "   Cannot build tree without FastTree"
    exit 1
fi

echo "Running FastTree phylogenetic analysis..."
echo "Input: $ALIGNED_FASTA"
echo "Output: $TREE_FILE"
echo "Model: GTR + Gamma"
echo "Bootstrap replicates: 1000"
echo ""
echo "This may take 1-2 hours depending on dataset size..."
echo ""

START_TIME=$(date +%s)

FastTree -nt -gtr -gamma -boot 1000 "$ALIGNED_FASTA" > "$TREE_FILE" 2>&1

FASTTREE_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

echo ""
if [ $FASTTREE_EXIT -eq 0 ] && [ -s "$TREE_FILE" ]; then
    echo "✅ FastTree completed in ${HOURS}h ${MINUTES}m"
    TREE_SIZE=$(stat -c%s "$TREE_FILE" 2>/dev/null || stat -f%z "$TREE_FILE")
    echo "   Tree file size: $((TREE_SIZE / 1024)) KB"
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
echo "🎉 PHYLOGENETIC ANALYSIS COMPLETE!"
echo "=========================================="
echo ""
echo "End time: $(date)"
echo ""
echo "📁 Output Directory: $OUTPUT_DIR"
echo ""
echo "📊 Output Files:"
echo "   Tree File:"
echo "     - prophage_tree.nwk (FastTree phylogeny)"
echo ""
echo "   Sequence Files:"
echo "     - prophages_all.fasta (all sequences from 2021-2024)"
if [ -f "$SUBSAMPLED_FASTA" ]; then
echo "     - prophages_subsampled.fasta (subsampled for analysis)"
fi
echo "     - prophages_aligned.fasta (MAFFT alignment)"
echo ""
echo "   Metadata:"
echo "     - prophage_metadata.tsv (year, sample ID, length)"
echo ""
echo "🌳 Next Steps:"
echo ""
echo "1. Download tree file:"
echo "   scp tylerdoe@beocat.ksu.edu:$OUTPUT_DIR/prophage_tree.nwk ."
echo "   scp tylerdoe@beocat.ksu.edu:$OUTPUT_DIR/prophage_metadata.tsv ."
echo ""
echo "2. Visualize with iTOL:"
echo "   - Go to https://itol.embl.de/"
echo "   - Upload prophage_tree.nwk"
echo "   - Upload prophage_metadata.tsv"
echo "   - Color by year (2021-2024) to see temporal patterns"
echo ""
echo "3. Or use FigTree:"
echo "   figtree prophage_tree.nwk"
echo ""
echo "4. Key questions to explore:"
echo "   - Do prophages cluster by year?"
echo "   - Are there E. coli-specific prophage lineages?"
echo "   - How does diversity change over 2021-2024?"
echo ""
echo "=========================================="

exit 0
