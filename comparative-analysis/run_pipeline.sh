#!/bin/bash
#
# Master script to run COMPASS comparative analysis pipeline
#
# Usage:
#   bash run_pipeline.sh
#
# This script will:
# 1. Extract data from COMPASS results (2022, 2023, 2024)
# 2. Integrate all data by sample ID
# 3. Run statistical analyses
# 4. Generate visualizations
#

set -e  # Exit on error

echo "=============================================="
echo "COMPASS Comparative Analysis Pipeline"
echo "Plasmid-Prophage-AMR Integration (2022-2024)"
echo "=============================================="
echo ""

# Check if running on Beocat
if [[ ! -d "/bulk/tylerdoe/archives" ]]; then
    echo "ERROR: This script must be run on Beocat"
    echo "Expected path /bulk/tylerdoe/archives not found"
    exit 1
fi

# Create directories
mkdir -p data results figures logs

# Activate Python environment (adjust path as needed)
if [[ -d "compass_analysis_env" ]]; then
    echo "Activating Python environment..."
    source compass_analysis_env/bin/activate
else
    echo "Warning: compass_analysis_env not found"
    echo "Run: python -m venv compass_analysis_env"
    echo "Then: source compass_analysis_env/bin/activate"
    echo "Then: pip install pandas numpy matplotlib seaborn networkx scipy"
    exit 1
fi

echo ""
echo "=============================================="
echo "Step 1: Extracting data from COMPASS results"
echo "=============================================="
echo ""

# Define years and paths
YEARS=("2022" "2023" "2024")
PATHS=(
    "/bulk/tylerdoe/archives/kansas_2022_ecoli"
    "/bulk/tylerdoe/archives/results_ecoli_2023"
    "/bulk/tylerdoe/archives/results_ecoli_all_2024"
)

for i in "${!YEARS[@]}"; do
    YEAR="${YEARS[$i]}"
    BASEPATH="${PATHS[$i]}"

    echo "Processing year $YEAR from $BASEPATH..."
    echo ""

    # Parse AMRFinder data
    echo "  Parsing AMRFinder results..."
    python scripts/parse_amrfinder.py \
        -i "$BASEPATH/amrfinder" \
        -o "data/amr_$YEAR.csv" \
        -y "$YEAR" \
        > "logs/parse_amr_$YEAR.log" 2>&1
    echo "    ✓ Saved to data/amr_$YEAR.csv"

    # Parse MOBsuite data
    echo "  Parsing MOBsuite (plasmid) results..."
    python scripts/parse_mobsuite.py \
        -i "$BASEPATH/mobsuite" \
        -o "data/plasmid_$YEAR.csv" \
        -y "$YEAR" \
        > "logs/parse_plasmid_$YEAR.log" 2>&1
    echo "    ✓ Saved to data/plasmid_$YEAR.csv"

    # Parse VIBRANT data
    echo "  Parsing VIBRANT (prophage) results..."
    python scripts/parse_vibrant.py \
        -i "$BASEPATH/vibrant" \
        -o "data/prophage_$YEAR.csv" \
        -y "$YEAR" \
        > "logs/parse_prophage_$YEAR.log" 2>&1
    echo "    ✓ Saved to data/prophage_$YEAR.csv"

    # Parse MLST data
    echo "  Parsing MLST results..."
    MLST_FILE="$BASEPATH/mlst/mlst_results.tsv"
    if [[ ! -f "$MLST_FILE" ]]; then
        # Try alternative filename
        MLST_FILE=$(find "$BASEPATH/mlst" -name "*.tsv" -type f | head -1)
    fi

    if [[ -f "$MLST_FILE" ]]; then
        python scripts/parse_mlst.py \
            -i "$MLST_FILE" \
            -o "data/mlst_$YEAR.csv" \
            -y "$YEAR" \
            > "logs/parse_mlst_$YEAR.log" 2>&1
        echo "    ✓ Saved to data/mlst_$YEAR.csv"
    else
        echo "    ⚠ MLST file not found, skipping"
    fi

    echo ""
done

echo "=============================================="
echo "Step 2: Integrating all data"
echo "=============================================="
echo ""

python scripts/integrate_data.py \
    --amr data/amr_2022.csv data/amr_2023.csv data/amr_2024.csv \
    --plasmids data/plasmid_2022.csv data/plasmid_2023.csv data/plasmid_2024.csv \
    --prophages data/prophage_2022.csv data/prophage_2023.csv data/prophage_2024.csv \
    --mlst data/mlst_2022.csv data/mlst_2023.csv data/mlst_2024.csv \
    --output results/integrated_summary.csv \
    | tee logs/integrate_data.log

echo ""
echo "✓ Integration complete!"
echo "  Output: results/integrated_summary.csv"
echo "  Output: results/integrated_summary_cooccurrence.csv"
echo ""

echo "=============================================="
echo "Step 3: Running analyses (TODO)"
echo "=============================================="
echo ""
echo "Analysis scripts will be added in next update..."
echo ""

echo "=============================================="
echo "Step 4: Generating visualizations (TODO)"
echo "=============================================="
echo ""
echo "Visualization scripts will be added in next update..."
echo ""

echo "=============================================="
echo "Pipeline Complete!"
echo "=============================================="
echo ""
echo "Results saved to:"
echo "  - data/ (extracted CSVs)"
echo "  - results/ (integrated data)"
echo "  - logs/ (processing logs)"
echo ""
echo "Next steps:"
echo "  1. Review results/integrated_summary.csv"
echo "  2. Check sample counts and data quality"
echo "  3. Run analysis scripts (when available)"
echo ""
echo "Check logs/ directory if any errors occurred"
echo ""
