#!/bin/bash
# ============================================================
# PREPARE DATA FOR AMR-PHAGE ANALYSIS
# ============================================================
# This script checks if your data directory has the required
# combined TSV files and creates them if needed
#

set -e  # Exit on error

KANSAS_DIR="/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"

echo "=========================================="
echo "Checking data structure for analysis"
echo "=========================================="
echo "Data directory: ${KANSAS_DIR}"
echo ""

# Check if directory exists
if [ ! -d "${KANSAS_DIR}" ]; then
    echo "❌ Error: Directory ${KANSAS_DIR} not found"
    exit 1
fi

echo "✅ Data directory found"
echo ""

# List subdirectories
echo "📁 Directory contents:"
ls -lh "${KANSAS_DIR}/" | head -20
echo ""

# Check for required subdirectories
echo "🔍 Checking for required data directories:"
for subdir in amrfinder vibrant assemblies metadata; do
    if [ -d "${KANSAS_DIR}/${subdir}" ]; then
        count=$(find "${KANSAS_DIR}/${subdir}" -type f | wc -l)
        echo "  ✅ ${subdir}/ exists (${count} files)"
    else
        echo "  ⚠️  ${subdir}/ not found"
    fi
done
echo ""

# Check for combined TSV files (required by analysis scripts)
echo "🔍 Checking for combined TSV files:"

if [ -f "${KANSAS_DIR}/amr_combined.tsv" ]; then
    lines=$(wc -l < "${KANSAS_DIR}/amr_combined.tsv")
    echo "  ✅ amr_combined.tsv exists (${lines} lines)"
else
    echo "  ❌ amr_combined.tsv NOT FOUND"
    echo ""
    echo "     This file needs to be created by combining AMRFinder results."
    echo "     Looking for individual AMR files..."
    amr_count=$(find "${KANSAS_DIR}/amrfinder" -name "*_amr.tsv" 2>/dev/null | wc -l || echo "0")
    echo "     Found ${amr_count} individual AMR result files"

    if [ "${amr_count}" -gt 0 ]; then
        echo ""
        echo "     To create amr_combined.tsv, you can use the pipeline's combine module"
        echo "     or manually concatenate the files with headers."
    fi
fi

if [ -f "${KANSAS_DIR}/vibrant_combined.tsv" ]; then
    lines=$(wc -l < "${KANSAS_DIR}/vibrant_combined.tsv")
    echo "  ✅ vibrant_combined.tsv exists (${lines} lines)"
else
    echo "  ❌ vibrant_combined.tsv NOT FOUND"
    echo ""
    echo "     This file needs to be created by combining VIBRANT results."
    echo "     Looking for VIBRANT directories..."
    vibrant_count=$(find "${KANSAS_DIR}/vibrant" -name "*_vibrant" -type d 2>/dev/null | wc -l || echo "0")
    echo "     Found ${vibrant_count} VIBRANT result directories"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="

required_files=0
found_files=0

if [ -f "${KANSAS_DIR}/amr_combined.tsv" ]; then
    ((found_files++))
fi
((required_files++))

if [ -f "${KANSAS_DIR}/vibrant_combined.tsv" ]; then
    ((found_files++))
fi
((required_files++))

echo "Required files: ${found_files}/${required_files}"
echo ""

if [ ${found_files} -eq ${required_files} ]; then
    echo "✅ All required files present! You can run the analysis scripts."
    echo ""
    echo "To run analyses:"
    echo "  sbatch run_kansas_2021-2025_analyses.sh"
    echo ""
else
    echo "⚠️  Some required files are missing."
    echo ""
    echo "The analysis scripts need these combined TSV files:"
    echo "  - ${KANSAS_DIR}/amr_combined.tsv"
    echo "  - ${KANSAS_DIR}/vibrant_combined.tsv"
    echo ""
    echo "Options to create them:"
    echo "  1. Re-run the COMPASS pipeline with the combine module"
    echo "  2. Manually create them by concatenating individual results"
    echo "  3. Use a Python script to parse and combine the results"
    echo ""
    echo "Would you like help creating a script to combine the results?"
fi
