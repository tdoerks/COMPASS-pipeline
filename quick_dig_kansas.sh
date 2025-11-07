#!/bin/bash
#
# Quick script to run deep dive analyses on Kansas E. coli results
# Auto-detects the Kansas results directory in your homes folder
#

echo "=========================================="
echo "Kansas E. coli Deep Dive Analysis"
echo "=========================================="

# Try to auto-detect Kansas results directory
POSSIBLE_PATHS=(
    "$HOME/kansas_ecoli_results"
    "$HOME/kansas_results"
    "$HOME/results/kansas"
    "$HOME/COMPASS/kansas"
    "/homes/tylerdoe/kansas_ecoli_results"
    "/homes/tylerdoe/kansas_results"
)

KANSAS_DIR=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path" ]; then
        # Check if it has year subdirectories
        if ls "$path"/202* >/dev/null 2>&1; then
            KANSAS_DIR="$path"
            echo "✅ Found Kansas results at: $KANSAS_DIR"
            break
        fi
    fi
done

if [ -z "$KANSAS_DIR" ]; then
    echo "❌ Could not auto-detect Kansas results directory"
    echo ""
    echo "Please provide the path to your Kansas results directory:"
    echo "  Usage: $0 /path/to/kansas_results"
    echo ""
    echo "Looking for a directory structure like:"
    echo "  kansas_results/"
    echo "    ├── 2021/"
    echo "    │   ├── amr_combined.tsv"
    echo "    │   └── vibrant_combined.tsv"
    echo "    ├── 2022/"
    echo "    ├── 2023/"
    echo "    └── ..."
    exit 1
fi

# Allow manual override
if [ ! -z "$1" ]; then
    KANSAS_DIR="$1"
    echo "Using specified directory: $KANSAS_DIR"
fi

echo ""
echo "Running analyses on: $KANSAS_DIR"
echo ""

# Get script directory (where this script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "=========================================="
echo "1. AMR Gene Enrichment Analysis"
echo "=========================================="
python3 "$SCRIPT_DIR/bin/analyze_enriched_amr_genes.py" "$KANSAS_DIR"
echo ""

echo "=========================================="
echo "2. dfrA51 Investigation (83% enrichment)"
echo "=========================================="
python3 "$SCRIPT_DIR/bin/investigate_dfra51.py" "$KANSAS_DIR"
echo ""

echo "=========================================="
echo "3. mdsA+mdsB Co-occurrence Analysis"
echo "=========================================="
python3 "$SCRIPT_DIR/bin/investigate_mdsa_mdsb.py" "$KANSAS_DIR"
echo ""

echo "=========================================="
echo "4. Deep Dive - All AMR on Prophage Contigs"
echo "=========================================="
python3 "$SCRIPT_DIR/bin/dig_amr_prophage_contigs.py" "$KANSAS_DIR"
echo ""

echo "=========================================="
echo "✅ All analyses complete!"
echo "=========================================="
echo ""
echo "Results saved to: $KANSAS_DIR"
echo ""
ls -lh "$KANSAS_DIR"/*.csv 2>/dev/null | tail -10
echo ""
echo "To view results:"
echo "  cd $KANSAS_DIR"
echo "  head -20 amr_enrichment_analysis.csv | column -t -s,"
echo ""
