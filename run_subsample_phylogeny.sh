#!/bin/bash
# Subsample prophages for phylogenetic analysis
# This reduces 3,369 prophages to a manageable number for tree building

echo "=========================================="
echo "Subsampling Prophages for Phylogeny"
echo "=========================================="
echo ""

# Set paths - UPDATE THESE if your results are in a different location
PHYLO_DIR="/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if phylogeny directory exists
if [ ! -d "$PHYLO_DIR" ]; then
    echo "❌ ERROR: Phylogeny directory not found: $PHYLO_DIR"
    echo ""
    echo "Please update PHYLO_DIR in this script to match your setup"
    exit 1
fi

cd "$PHYLO_DIR"

# Check if input files exist
if [ ! -f "complete_prophages.fasta" ]; then
    echo "❌ ERROR: complete_prophages.fasta not found"
    echo "   Run: python3 bin/prepare_prophage_phylogeny.py"
    exit 1
fi

if [ ! -f "prophage_metadata.tsv" ]; then
    echo "❌ ERROR: prophage_metadata.tsv not found"
    exit 1
fi

# Count original sequences
n_orig=$(grep -c "^>" complete_prophages.fasta)
echo "Original sequences: $n_orig"
echo ""

# Run subsampling
echo "Running subsample script..."
echo "Strategy: representative (balanced across years and organisms)"
echo "Target: 200 sequences"
echo ""

python3 "$SCRIPT_DIR/bin/subsample_prophages_for_phylogeny.py" \
    --strategy representative \
    --n 200 \
    --input-fasta "$PHYLO_DIR/complete_prophages.fasta" \
    --input-metadata "$PHYLO_DIR/prophage_metadata.tsv" \
    --output-fasta "$PHYLO_DIR/subsample_prophages.fasta" \
    --output-metadata "$PHYLO_DIR/subsample_metadata.tsv"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Subsampling complete!"
    echo "=========================================="
    echo ""
    echo "Output files:"
    echo "  - subsample_prophages.fasta"
    echo "  - subsample_metadata.tsv"
    echo ""
    echo "Next steps:"
    echo "  1. Align: bash run_align_subsample.sh"
    echo "  2. Build tree: sbatch build_phylogeny_subsample.slurm"
    echo ""
else
    echo ""
    echo "❌ Subsampling failed with exit code $exit_code"
fi

exit $exit_code
