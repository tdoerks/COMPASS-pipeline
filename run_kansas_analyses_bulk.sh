#!/bin/bash
#SBATCH --job-name=kansas_analysis
#SBATCH --output=/bulk/tylerdoe/archives/kansas_analysis_%j.out
#SBATCH --error=/bulk/tylerdoe/archives/kansas_analysis_%j.err
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# ============================================================
# RUN ALL AMR-PHAGE ANALYSES ON KANSAS 2021-2025 DATASET
# ============================================================
# This script runs all analysis scripts on the Kansas 2021-2025
# NARMS dataset located in /bulk/tylerdoe/archives
#

# Set directories
KANSAS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"
PIPELINE_DIR="/bulk/tylerdoe/archives/COMPASS-pipeline"  # Adjust if different

# Create analysis output directory
OUTPUT_DIR="${KANSAS_DIR}/analysis_results"
mkdir -p "${OUTPUT_DIR}"

# Load required modules
module load Python/3.9 2>/dev/null || module load Anaconda3 2>/dev/null || echo "⚠️ Python module not loaded - using system Python"

echo "=========================================="
echo "AMR-Phage Analysis Suite"
echo "Kansas 2021-2025 NARMS Dataset"
echo "=========================================="
echo "Input directory: ${KANSAS_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo "Pipeline directory: ${PIPELINE_DIR}"
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Change to pipeline directory
cd "${PIPELINE_DIR}" || exit 1

# Check for required combined files
echo "🔍 Checking for required input files..."
if [ ! -f "${KANSAS_DIR}/amr_combined.tsv" ]; then
    echo "  ❌ ERROR: amr_combined.tsv not found"
    echo "  Run: bash create_combined_files.sh"
    exit 1
fi

if [ ! -f "${KANSAS_DIR}/vibrant_combined.tsv" ]; then
    echo "  ❌ ERROR: vibrant_combined.tsv not found"
    echo "  Run: bash create_combined_files.sh"
    exit 1
fi

echo "  ✅ Both required files found"
echo ""

# ============================================================
# RUN ANALYSES
# ============================================================

# 1. AMR Gene Enrichment Analysis
echo "📊 [1/6] Running AMR gene enrichment analysis..."
echo "  This identifies which genes show highest % on prophage contigs"
python3 bin/analyze_enriched_amr_genes.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/01_enrichment_analysis.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/amr_enrichment_analysis.csv"
else
    echo "  ❌ FAILED - check ${OUTPUT_DIR}/01_enrichment_analysis.log"
fi
echo ""

# 2. Deep Dive into AMR-Prophage Contigs
echo "🔬 [2/6] Running deep dive on AMR-prophage shared contigs..."
python3 bin/dig_amr_prophage_contigs.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/02_deep_dive.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/kansas_amr_prophage_contigs_DEEP_DIVE.csv"
else
    echo "  ❌ FAILED - check ${OUTPUT_DIR}/02_deep_dive.log"
fi
echo ""

# 3. Investigate dfrA51 (if present)
echo "🔍 [3/6] Investigating dfrA51 (trimethoprim resistance)..."
python3 bin/investigate_dfra51.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/03_dfra51.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/dfra51_investigation.csv"
else
    echo "  ⚠️ Skipped or failed - check ${OUTPUT_DIR}/03_dfra51.log"
fi
echo ""

# 4. Investigate mdsA+mdsB co-occurrence
echo "🧬 [4/6] Investigating mdsA+mdsB co-occurrence..."
python3 bin/investigate_mdsa_mdsb.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/04_mdsa_mdsb.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/mdsa_mdsb_investigation.csv"
else
    echo "  ⚠️ Skipped or failed - check ${OUTPUT_DIR}/04_mdsa_mdsb.log"
fi
echo ""

# 5. Comprehensive AMR Analysis
echo "📈 [5/6] Running comprehensive AMR-phage-mobile element analysis..."
python3 bin/comprehensive_amr_analysis.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/05_comprehensive.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/kansas_comprehensive_amr_analysis.html"
else
    echo "  ❌ FAILED - check ${OUTPUT_DIR}/05_comprehensive.log"
fi
echo ""

# 6. AMR-Mobile Elements Analysis
echo "🧩 [6/6] Running AMR-mobile element association analysis..."
python3 bin/analyze_amr_mobile_elements.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/06_mobile_elements.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/amr_mobile_element_analysis.csv"
else
    echo "  ❌ FAILED - check ${OUTPUT_DIR}/06_mobile_elements.log"
fi
echo ""

# ============================================================
# SUMMARY
# ============================================================

echo "=========================================="
echo "Analysis Complete!"
echo "=========================================="
echo "End time: $(date)"
echo ""

# Count successful outputs
success_count=0
[ -f "${KANSAS_DIR}/amr_enrichment_analysis.csv" ] && ((success_count++))
[ -f "${KANSAS_DIR}/kansas_amr_prophage_contigs_DEEP_DIVE.csv" ] && ((success_count++))
[ -f "${KANSAS_DIR}/kansas_comprehensive_amr_analysis.html" ] && ((success_count++))
[ -f "${KANSAS_DIR}/amr_mobile_element_analysis.csv" ] && ((success_count++))

echo "Successfully created $success_count / 4 core output files"
echo ""

if [ $success_count -eq 4 ]; then
    echo "✅ All core analyses completed successfully!"
else
    echo "⚠️ Some analyses failed - check log files in:"
    echo "   ${OUTPUT_DIR}/"
fi

echo ""
echo "Output files in ${KANSAS_DIR}:"
ls -lh "${KANSAS_DIR}"/*.csv "${KANSAS_DIR}"/*.html 2>/dev/null
echo ""

echo "Log files in ${OUTPUT_DIR}:"
ls -lh "${OUTPUT_DIR}"/*.log
echo ""

echo "To view results:"
echo "  cd ${KANSAS_DIR}"
echo "  less amr_enrichment_analysis.csv"
echo ""
echo "To download HTML report to your computer:"
echo "  scp tylerdoe@icr-helios:${KANSAS_DIR}/kansas_comprehensive_amr_analysis.html ."
echo ""
