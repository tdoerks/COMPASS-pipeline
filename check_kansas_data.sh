#!/bin/bash
# ============================================================
# CHECK KANSAS 2021-2025 DATA STRUCTURE
# ============================================================

KANSAS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"

echo "=========================================="
echo "Kansas 2021-2025 Data Structure Check"
echo "=========================================="
echo "Data directory: ${KANSAS_DIR}"
echo ""

# Check if directory exists
if [ ! -d "${KANSAS_DIR}" ]; then
    echo "❌ Error: Directory not found"
    exit 1
fi

echo "✅ Directory found"
echo ""

# List all subdirectories with counts
echo "📁 Subdirectories and file counts:"
echo "----------------------------------------"
for dir in abricate amrfinder assemblies diamond_prophage fastp fastq fastqc \
           filtered_samples metadata mlst mobsuite multiqc phanotate \
           pipeline_info quast sistr trimmed_fastq vibrant; do
    if [ -d "${KANSAS_DIR}/${dir}" ]; then
        count=$(find "${KANSAS_DIR}/${dir}" -type f 2>/dev/null | wc -l)
        size=$(du -sh "${KANSAS_DIR}/${dir}" 2>/dev/null | cut -f1)
        printf "  %-20s %6d files   %8s\n" "${dir}/" "$count" "$size"
    fi
done
echo ""

# Check for combined TSV files
echo "🔍 Checking for combined TSV files (needed for analysis):"
echo "----------------------------------------"

if [ -f "${KANSAS_DIR}/amr_combined.tsv" ]; then
    lines=$(wc -l < "${KANSAS_DIR}/amr_combined.tsv")
    echo "  ✅ amr_combined.tsv EXISTS (${lines} lines)"
else
    echo "  ❌ amr_combined.tsv NOT FOUND"
    echo "     Need to create from: amrfinder/*_amr.tsv"
fi

if [ -f "${KANSAS_DIR}/vibrant_combined.tsv" ]; then
    lines=$(wc -l < "${KANSAS_DIR}/vibrant_combined.tsv")
    echo "  ✅ vibrant_combined.tsv EXISTS (${lines} lines)"
else
    echo "  ❌ vibrant_combined.tsv NOT FOUND"
    echo "     Need to create from: vibrant/*_vibrant/VIBRANT_*/quality files"
fi
echo ""

# Sample some individual result files
echo "📊 Sample individual result files:"
echo "----------------------------------------"

# AMRFinder files
amr_files=$(find "${KANSAS_DIR}/amrfinder" -name "*_amr.tsv" 2>/dev/null | head -3)
if [ -n "$amr_files" ]; then
    amr_count=$(find "${KANSAS_DIR}/amrfinder" -name "*_amr.tsv" 2>/dev/null | wc -l)
    echo "  AMRFinder results: ${amr_count} files"
    echo "  Example files:"
    echo "$amr_files" | while read f; do echo "    $(basename $f)"; done
else
    echo "  ⚠️ No AMRFinder *_amr.tsv files found"
fi
echo ""

# VIBRANT directories
vibrant_dirs=$(find "${KANSAS_DIR}/vibrant" -maxdepth 1 -type d -name "*_vibrant" 2>/dev/null | head -3)
if [ -n "$vibrant_dirs" ]; then
    vibrant_count=$(find "${KANSAS_DIR}/vibrant" -maxdepth 1 -type d -name "*_vibrant" 2>/dev/null | wc -l)
    echo "  VIBRANT results: ${vibrant_count} directories"
    echo "  Example directories:"
    echo "$vibrant_dirs" | while read d; do echo "    $(basename $d)"; done
else
    echo "  ⚠️ No VIBRANT *_vibrant directories found"
fi
echo ""

# MLST files (to estimate total samples)
mlst_count=$(find "${KANSAS_DIR}/mlst" -name "*.tsv" 2>/dev/null | wc -l)
echo "  MLST results: ${mlst_count} files (estimated sample count)"
echo ""

# Check metadata
echo "📋 Metadata files:"
echo "----------------------------------------"
if [ -d "${KANSAS_DIR}/metadata" ]; then
    ls -lh "${KANSAS_DIR}/metadata/"*.csv 2>/dev/null
else
    echo "  No metadata directory found"
fi
echo ""

# Summary
echo "=========================================="
echo "Summary & Next Steps"
echo "=========================================="

combined_exists=0
[ -f "${KANSAS_DIR}/amr_combined.tsv" ] && ((combined_exists++))
[ -f "${KANSAS_DIR}/vibrant_combined.tsv" ] && ((combined_exists++))

if [ $combined_exists -eq 2 ]; then
    echo "✅ Both combined TSV files exist!"
    echo ""
    echo "Ready to run analysis scripts:"
    echo "  cd /bulk/tylerdoe/archives/COMPASS-pipeline"
    echo "  sbatch run_kansas_2021-2025_analyses.sh"
elif [ $combined_exists -eq 1 ]; then
    echo "⚠️ Only 1 of 2 combined files exists"
    echo ""
    echo "Need to create missing file(s)"
    echo "Run: bash create_combined_files.sh"
else
    echo "❌ No combined TSV files found"
    echo ""
    echo "Need to create both combined files from individual results"
    echo "Run: bash create_combined_files.sh"
fi
echo ""
