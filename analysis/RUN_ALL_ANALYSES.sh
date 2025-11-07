#!/bin/bash
#
# RUN ALL AMR-PHAGE ANALYSES ON BEOCAT
# =====================================
# This script runs all analysis scripts on the Kansas E. coli results
# Run this on Beocat after connecting via SSH
#

# Set base directory for Kansas results (multi-year structure)
KANSAS_DIR="/bulk/tylerdoe/kansas_results"

# Create analysis output directory
OUTPUT_DIR="${KANSAS_DIR}/analysis_results"
mkdir -p "${OUTPUT_DIR}"

echo "=========================================="
echo "Running AMR-Phage Analysis Suite"
echo "=========================================="
echo "Input directory: ${KANSAS_DIR}"
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# 1. AMR Gene Enrichment Analysis
echo "📊 [1/4] Running AMR gene enrichment analysis..."
echo "  This identifies which genes show highest % on prophage contigs"
python3 bin/analyze_enriched_amr_genes.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/01_enrichment_analysis.log" 2>&1
echo "  ✅ Complete. Output: ${KANSAS_DIR}/amr_enrichment_analysis.csv"
echo ""

# 2. Deep Dive into AMR-Prophage Contigs
echo "🔬 [2/4] Running deep dive on AMR-prophage shared contigs..."
echo "  This analyzes the 9.66% of AMR genes on prophage-containing contigs"
python3 bin/dig_amr_prophage_contigs.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/02_deep_dive.log" 2>&1
echo "  ✅ Complete. Output: ${KANSAS_DIR}/kansas_amr_prophage_contigs_DEEP_DIVE.csv"
echo ""

# 3. Comprehensive AMR Analysis (includes mobile elements when MOB-suite fixed)
echo "🧬 [3/4] Running comprehensive AMR-phage-mobile element analysis..."
echo "  This combines physical co-location, mobile elements, and sample patterns"
python3 bin/comprehensive_amr_analysis.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/03_comprehensive.log" 2>&1
echo "  ✅ Complete. Output: ${KANSAS_DIR}/kansas_comprehensive_amr_analysis.html"
echo ""

# 4. AMR-Mobile Elements Analysis (plasmids, integrases, transposases)
echo "🧩 [4/4] Running AMR-mobile element association analysis..."
echo "  This analyzes AMR associations with plasmids and other mobile elements"
python3 bin/analyze_amr_mobile_elements.py "${KANSAS_DIR}" > "${OUTPUT_DIR}/04_mobile_elements.log" 2>&1
echo "  ✅ Complete. Output: ${KANSAS_DIR}/amr_mobile_element_analysis.csv"
echo ""

echo "=========================================="
echo "✅ All analyses complete!"
echo "=========================================="
echo ""
echo "Output files created in ${KANSAS_DIR}:"
echo "  1. amr_enrichment_analysis.csv - Gene enrichment statistics"
echo "  2. highly_enriched_amr_occurrences.csv - Individual occurrences of enriched genes"
echo "  3. kansas_amr_prophage_contigs_DEEP_DIVE.csv - Detailed AMR-prophage contig analysis"
echo "  4. kansas_comprehensive_amr_analysis.html - Interactive HTML report"
echo "  5. amr_mobile_element_analysis.csv - Mobile element associations"
echo ""
echo "Log files saved to: ${OUTPUT_DIR}/"
echo ""
echo "Key findings to review:"
echo "  • dfrA51: 83.3% on prophage contigs (trimethoprim resistance)"
echo "  • glpT_E448K: 34.6% on prophage contigs (fosfomycin resistance)"
echo "  • FOSFOMYCIN class: 32.1% enrichment on prophage contigs"
echo "  • Ground Beef: Highest AMR-prophage association (13.4%)"
echo "  • mdsA+mdsB: Co-occur 18 times on same prophage contig"
echo ""
echo "To view HTML report, copy to your local machine:"
echo "  scp tylerdoe@beocat.cis.ksu.edu:${KANSAS_DIR}/kansas_comprehensive_amr_analysis.html ."
echo ""
