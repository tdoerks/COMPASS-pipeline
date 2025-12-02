#!/bin/bash
# Align subsampled prophages with MAFFT

echo "=========================================="
echo "Aligning Subsampled Prophages with MAFFT"
echo "=========================================="
echo ""

# Set paths
PHYLO_DIR="/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny"

# Check if phylogeny directory exists
if [ ! -d "$PHYLO_DIR" ]; then
    echo "❌ ERROR: Phylogeny directory not found: $PHYLO_DIR"
    exit 1
fi

cd "$PHYLO_DIR"

# Check if subsampled file exists
if [ ! -f "subsample_prophages.fasta" ]; then
    echo "❌ ERROR: subsample_prophages.fasta not found"
    echo "   Run: bash run_subsample_phylogeny.sh first"
    exit 1
fi

# Count sequences
n_seqs=$(grep -c "^>" subsample_prophages.fasta)
file_size=$(du -h subsample_prophages.fasta | cut -f1)

echo "Sequences to align: $n_seqs"
echo "File size: $file_size"
echo ""

# Check if MAFFT is available
if ! command -v mafft &> /dev/null; then
    echo "⚠️  MAFFT not found, trying to load module..."

    if module load MAFFT 2>/dev/null || module load mafft 2>/dev/null; then
        echo "✅ Loaded MAFFT module"
    else
        echo "❌ ERROR: MAFFT not available"
        echo "   Please install MAFFT or load the appropriate module"
        exit 1
    fi
fi

echo "MAFFT version:"
mafft --version
echo ""

echo "Starting alignment..."
echo "This may take 10-30 minutes for $n_seqs sequences..."
echo ""

# Run MAFFT
# --auto: automatically choose alignment strategy
# --thread 8: use 8 threads (adjust based on your system)
mafft --auto --thread 8 subsample_prophages.fasta > subsample_aligned.fasta

exit_code=$?

if [ $exit_code -eq 0 ]; then
    aligned_size=$(du -h subsample_aligned.fasta | cut -f1)
    echo ""
    echo "=========================================="
    echo "✅ Alignment complete!"
    echo "=========================================="
    echo ""
    echo "Output file: subsample_aligned.fasta ($aligned_size)"
    echo ""
    echo "Next step:"
    echo "  Build tree: sbatch build_phylogeny_subsample.slurm"
    echo ""
else
    echo ""
    echo "❌ Alignment failed with exit code $exit_code"
fi

exit $exit_code
