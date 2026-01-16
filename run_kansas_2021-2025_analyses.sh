#!/bin/bash
#SBATCH --job-name=kansas_amr_analysis
#SBATCH --output=kansas_analysis_%j.out
#SBATCH --error=kansas_analysis_%j.err
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# ============================================================
# RUN ALL AMR-PHAGE ANALYSES ON KANSAS 2021-2025 DATASET
# ============================================================
# This script runs all analysis scripts on the Kansas 2021-2025
# NARMS dataset located in /fastscratch/tylerdoe
#

# Set base directory for Kansas results
KANSAS_DIR="/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"

# Create analysis output directory
OUTPUT_DIR="${KANSAS_DIR}/analysis_results"
mkdir -p "${OUTPUT_DIR}"

# Load required modules (adjust as needed for your HPC)
module load Python/3.9 2>/dev/null || echo "Python module not loaded"

echo "=========================================="
echo "Running AMR-Phage Analysis Suite"
echo "=========================================="
echo "Input directory: ${KANSAS_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo "Pipeline directory: ${PIPELINE_DIR}"
echo ""

# Change to pipeline directory
cd "${PIPELINE_DIR}" || exit 1

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
echo "  This analyzes AMR genes on prophage-containing contigs"
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
    echo "  ⚠️  Skipped or failed - check ${OUTPUT_DIR}/03_dfra51.log"
fi
echo ""

# 4. Investigate mdsA+mdsB co-occurrence
echo "🧬 [4/6] Investigating mdsA+mdsB co-occurrence..."
python3 bin/investigate_mdsa_mdsb.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/04_mdsa_mdsb.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/mdsa_mdsb_investigation.csv"
else
    echo "  ⚠️  Skipped or failed - check ${OUTPUT_DIR}/04_mdsa_mdsb.log"
fi
echo ""

# 5. Comprehensive AMR Analysis (includes mobile elements)
echo "📈 [5/6] Running comprehensive AMR-phage-mobile element analysis..."
echo "  This combines physical co-location, mobile elements, and sample patterns"
python3 bin/comprehensive_amr_analysis.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/05_comprehensive.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/kansas_comprehensive_amr_analysis.html"
else
    echo "  ❌ FAILED - check ${OUTPUT_DIR}/05_comprehensive.log"
fi
echo ""

# 6. AMR-Mobile Elements Analysis
echo "🧩 [6/6] Running AMR-mobile element association analysis..."
echo "  This analyzes AMR associations with plasmids and other mobile elements"
python3 bin/analyze_amr_mobile_elements.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/06_mobile_elements.log" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Complete. Output: ${KANSAS_DIR}/amr_mobile_element_analysis.csv"
else
    echo "  ❌ FAILED - check ${OUTPUT_DIR}/06_mobile_elements.log"
fi
echo ""

echo "=========================================="
echo "✅ All analyses complete!"
echo "=========================================="
echo ""
echo "Output files created in ${KANSAS_DIR}:"
echo "  1. amr_enrichment_analysis.csv - Gene enrichment statistics"
echo "  2. highly_enriched_amr_occurrences.csv - Individual occurrences of enriched genes"
echo "  3. dfra51_investigation.csv - dfrA51 deep dive (if present)"
echo "  4. mdsa_mdsb_investigation.csv - mdsA+mdsB co-occurrence (if present)"
echo "  5. kansas_amr_prophage_contigs_DEEP_DIVE.csv - Detailed AMR-prophage contig analysis"
echo "  6. kansas_comprehensive_amr_analysis.html - Interactive HTML report"
echo "  7. amr_mobile_element_analysis.csv - Mobile element associations"
echo ""
echo "Log files saved to: ${OUTPUT_DIR}/"
echo ""
echo "To view results:"
echo "  cd ${KANSAS_DIR}"
echo "  ls -lh *.csv *.html"
echo ""
