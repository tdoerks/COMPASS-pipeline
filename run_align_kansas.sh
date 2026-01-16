#!/bin/bash
# Align Kansas prophage sequences with MAFFT
# This script prepares aligned sequences for phylogenetic tree construction

echo "=========================================="
echo "Kansas Prophage Sequence Alignment"
echo "=========================================="
echo ""

# Set paths
PHYLO_DIR="/bulk/tylerdoe/archives/compass_kansas_results/phylogeny"
INPUT_FASTA="kansas_complete_prophages.fasta"
OUTPUT_FASTA="kansas_aligned.fasta"

# Check if running from correct directory or navigate there
if [ -f "$INPUT_FASTA" ]; then
    echo "Running in current directory"
elif [ -f "$PHYLO_DIR/$INPUT_FASTA" ]; then
    echo "Navigating to $PHYLO_DIR"
    cd "$PHYLO_DIR"
else
    echo "❌ ERROR: $INPUT_FASTA not found"
    echo ""
    echo "Please run preparation script first:"
    echo "  python3 prepare_kansas_phylogeny.py --output-dir $PHYLO_DIR"
    exit 1
fi

# Count sequences
n_seqs=$(grep -c "^>" "$INPUT_FASTA")
echo "Number of sequences: $n_seqs"

# Check file size
file_size=$(du -h "$INPUT_FASTA" | cut -f1)
echo "FASTA size: $file_size"
echo ""

# Determine if we need subsampling
if [ $n_seqs -gt 500 ]; then
    echo "⚠️  WARNING: You have $n_seqs sequences"
    echo "   Alignment will be VERY slow (could take 12+ hours)"
    echo ""
    echo "Recommendations:"
    echo "  1. Subsample first (see subsample script)"
    echo "  2. Or run this as a SLURM job with high memory"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Please subsample first."
        exit 0
    fi
fi

# Check if MAFFT is available
if ! command -v mafft &> /dev/null; then
    echo "❌ ERROR: MAFFT not found"
    echo ""
    echo "Please install MAFFT:"
    echo "  module load MAFFT  (on Beocat)"
    echo "  conda install -c bioconda mafft  (via conda)"
    exit 1
fi

echo "MAFFT version:"
mafft --version 2>&1 | head -1
echo ""

echo "=========================================="
echo "Starting alignment..."
echo "=========================================="
echo ""
echo "This may take a while depending on number of sequences:"
echo "  - 50 sequences: ~5 minutes"
echo "  - 200 sequences: ~30 minutes"
echo "  - 500 sequences: ~2-4 hours"
echo "  - 1000+ sequences: ~12+ hours"
echo ""

# Run MAFFT
# --auto: automatically select best algorithm
# --thread 16: use 16 threads (adjust based on available cores)
# --adjustdirection: allow reverse complement (important for phages!)

mafft --auto --thread 16 --adjustdirection "$INPUT_FASTA" > "$OUTPUT_FASTA"

exit_code=$?

echo ""
echo "=========================================="
echo "Alignment Complete"
echo "=========================================="

if [ $exit_code -eq 0 ]; then
    aligned_size=$(du -h "$OUTPUT_FASTA" | cut -f1)
    echo "✅ SUCCESS!"
    echo ""
    echo "Output: $OUTPUT_FASTA (size: $aligned_size)"
    echo ""
    echo "Next step:"
    echo "  sbatch build_phylogeny_kansas.slurm"
else
    echo "❌ ERROR: MAFFT failed with exit code $exit_code"
fi

echo "=========================================="

exit $exit_code
