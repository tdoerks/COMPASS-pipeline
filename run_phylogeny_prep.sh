#!/bin/bash
# Run Kansas prophage phylogeny preparation
# This script is designed to run in a screen session

echo "=========================================="
echo "Kansas Prophage Phylogeny Preparation"
echo "=========================================="
echo "Start time: $(date)"
echo ""

# Set paths
RESULTS_DIR="/bulk/tylerdoe/archives/compass_kansas_results"
OUTPUT_DIR="/bulk/tylerdoe/archives/compass_kansas_results/phylogeny"
SCRIPT_PATH="$HOME/COMPASS-pipeline/prepare_kansas_phylogeny.py"

# Check if we're in the right directory
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "❌ ERROR: Output directory not found: $OUTPUT_DIR"
    echo "   Please create it first: mkdir -p $OUTPUT_DIR"
    exit 1
fi

cd "$OUTPUT_DIR"
echo "Working directory: $(pwd)"
echo ""

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ ERROR: Script not found: $SCRIPT_PATH"
    echo "   Please pull latest changes from v1.2-mod branch"
    exit 1
fi

# Run the preparation script
echo "Running prophage extraction..."
echo ""

python3 "$SCRIPT_PATH" \
    --results-dir "$RESULTS_DIR" \
    --output-dir "$OUTPUT_DIR"

exit_code=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $exit_code"
echo "=========================================="

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS!"
    echo ""
    echo "Next steps:"
    echo ""

    # Check how many sequences we got
    if [ -f "kansas_complete_prophages.fasta" ]; then
        n_seqs=$(grep -c "^>" kansas_complete_prophages.fasta)
        echo "Total prophages extracted: $n_seqs"
        echo ""

        if [ $n_seqs -gt 500 ]; then
            echo "⚠️  Large dataset detected ($n_seqs sequences)"
            echo "   Recommendation: Subsample before alignment"
            echo ""
            echo "   Run:"
            echo "   python3 ~/COMPASS-pipeline/bin/subsample_prophages_for_phylogeny.py \\"
            echo "       --strategy representative \\"
            echo "       --n 200 \\"
            echo "       --input-fasta kansas_complete_prophages.fasta \\"
            echo "       --input-metadata kansas_prophage_metadata.tsv \\"
            echo "       --output-fasta kansas_subsample.fasta \\"
            echo "       --output-metadata kansas_subsample_metadata.tsv"
            echo ""
        else
            echo "📊 Dataset size is manageable ($n_seqs sequences)"
            echo "   You can proceed directly to alignment"
            echo ""
            echo "   Run:"
            echo "   bash ~/COMPASS-pipeline/run_align_kansas.sh"
            echo ""
        fi
    fi

    echo "See PHYLOGENY_README.md for full documentation"
else
    echo "❌ FAILED with exit code $exit_code"
    echo "   Check output above for errors"
fi

echo "=========================================="

exit $exit_code
