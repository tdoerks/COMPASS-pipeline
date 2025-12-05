#!/bin/bash
# ============================================================
# CREATE COMBINED TSV FILES FOR ANALYSIS
# ============================================================
# This script combines individual AMRFinder and VIBRANT results
# into single TSV files required by the analysis scripts
#
# Usage: ./create_combined_files.sh [data_directory]
#   If no directory specified, uses: /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod
#
# Example:
#   ./create_combined_files.sh /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod
#

set -e  # Exit on error

# Check if directory is passed as argument, otherwise use default
KANSAS_DIR="${1:-/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod}"

echo "=========================================="
echo "Creating Combined TSV Files"
echo "=========================================="
echo "Data directory: ${KANSAS_DIR}"
echo ""

cd "${KANSAS_DIR}" || exit 1

# ============================================================
# 1. COMBINE AMRFinder RESULTS
# ============================================================

echo "📊 [1/2] Combining AMRFinder results..."
echo "----------------------------------------"

AMR_OUTPUT="amr_combined.tsv"

# Build array of AMR files
echo "  Finding AMRFinder files..."
mapfile -t amr_file_array < <(find amrfinder -name "*_amr.tsv" 2>/dev/null | sort)
amr_count=${#amr_file_array[@]}

if [ $amr_count -eq 0 ]; then
    echo "  ❌ No AMRFinder files found!"
    exit 1
fi

echo "  Found ${amr_count} AMRFinder result files"

# Get header from first file and add sample_id column
first_file="${amr_file_array[0]}"
echo "  Using header from: $(basename $first_file)"

# Write header with sample_id prepended
echo -ne "sample_id\t" > "${AMR_OUTPUT}"
head -1 "$first_file" >> "${AMR_OUTPUT}"

# Process each file
echo "  Processing files..."
for i in "${!amr_file_array[@]}"; do
    amr_file="${amr_file_array[$i]}"

    # Extract sample ID from filename (e.g., SRR12345678_amr.tsv -> SRR12345678)
    sample_id=$(basename "$amr_file" | sed 's/_amr\.tsv$//')

    # Add all data lines with sample_id prepended
    tail -n +2 "$amr_file" | awk -v sid="$sample_id" 'BEGIN{OFS="\t"} {print sid, $0}' >> "${AMR_OUTPUT}"

    if [ $(((i+1) % 50)) -eq 0 ]; then
        echo "    Processed $((i+1)) / $amr_count files..."
    fi
done

total_lines=$(wc -l < "${AMR_OUTPUT}")
data_lines=$((total_lines - 1))

echo "  ✅ Created: ${AMR_OUTPUT}"
echo "     Total lines: ${total_lines} (${data_lines} data + 1 header)"
echo ""

# ============================================================
# 2. COMBINE VIBRANT RESULTS
# ============================================================

echo "🦠 [2/2] Combining VIBRANT results..."
echo "----------------------------------------"

VIBRANT_OUTPUT="vibrant_combined.tsv"

# Build array of VIBRANT directories
echo "  Finding VIBRANT directories..."
mapfile -t vibrant_dir_array < <(find vibrant -maxdepth 1 -type d -name "*_vibrant" 2>/dev/null | sort)
vibrant_count=${#vibrant_dir_array[@]}

if [ $vibrant_count -eq 0 ]; then
    echo "  ❌ No VIBRANT directories found!"
    exit 1
fi

echo "  Found ${vibrant_count} VIBRANT result directories"

# Create header
echo -e "sample_id\tscaffold\tfragment\tprotein\tkeywords\ttype\tquality\tcompleteness\tcontig_id" > "${VIBRANT_OUTPUT}"

# Process each VIBRANT directory
found_results=0
echo "  Processing directories..."
for i in "${!vibrant_dir_array[@]}"; do
    vdir="${vibrant_dir_array[$i]}"

    # Extract sample ID from directory name
    sample_id=$(basename "$vdir" | sed 's/_vibrant$//')

    # Find VIBRANT quality file using expected path pattern (faster than find)
    # Path pattern: {sample}_vibrant/VIBRANT_{sample}_contigs/VIBRANT_results_{sample}_contigs/VIBRANT_genome_quality_{sample}_contigs.tsv
    quality_file="${vdir}/VIBRANT_${sample_id}_contigs/VIBRANT_results_${sample_id}_contigs/VIBRANT_genome_quality_${sample_id}_contigs.tsv"

    if [ -f "$quality_file" ]; then
        # Add data lines with sample_id prepended
        tail -n +2 "$quality_file" | awk -v sid="$sample_id" 'BEGIN{OFS="\t"} {print sid, $0}' >> "${VIBRANT_OUTPUT}"
        ((found_results++))
    fi

    # Show progress more frequently - every 25 directories
    if [ $(((i+1) % 25)) -eq 0 ]; then
        echo "    Processed $((i+1)) / $vibrant_count directories (found results in $found_results)..."
    fi
done

total_lines=$(wc -l < "${VIBRANT_OUTPUT}")
data_lines=$((total_lines - 1))

echo "  ✅ Created: ${VIBRANT_OUTPUT}"
echo "     Processed ${processed} directories"
echo "     Found results in ${found_results} samples"
echo "     Total lines: ${total_lines} (${data_lines} prophages + 1 header)"
echo ""

# ============================================================
# VERIFICATION
# ============================================================

echo "=========================================="
echo "✅ Combined Files Created Successfully!"
echo "=========================================="
echo ""
echo "Created files:"
echo "  ${KANSAS_DIR}/${AMR_OUTPUT}"
echo "  ${KANSAS_DIR}/${VIBRANT_OUTPUT}"
echo ""
echo "File sizes:"
ls -lh "${AMR_OUTPUT}" "${VIBRANT_OUTPUT}"
echo ""

# Quick preview
echo "Preview of amr_combined.tsv (first 3 data lines):"
head -4 "${AMR_OUTPUT}" | cut -f1-5 | column -t -s $'\t'
echo ""

echo "Preview of vibrant_combined.tsv (first 3 data lines):"
head -4 "${VIBRANT_OUTPUT}" | cut -f1-6 | column -t -s $'\t'
echo ""

echo "=========================================="
echo "🎉 Ready to Run Analysis!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Verify the combined files look correct (check previews above)"
echo "  2. Run the analysis scripts:"
echo ""
echo "     cd /bulk/tylerdoe/archives/COMPASS-pipeline"
echo "     sbatch run_kansas_2021-2025_analyses.sh"
echo ""
echo "  3. Or test with a single analysis first:"
echo ""
echo "     python3 bin/analyze_enriched_amr_genes.py ${KANSAS_DIR}"
echo ""
