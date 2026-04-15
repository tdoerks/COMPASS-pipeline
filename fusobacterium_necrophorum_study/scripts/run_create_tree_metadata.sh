#!/bin/bash
#
# Run on Beocat to create tree sample metadata table
#
# This creates a comprehensive supplementary file with all metadata
# for samples that appear in the prophage tree
#

set -e

echo "========================================================================"
echo "Creating Tree Sample Metadata Table"
echo "========================================================================"
echo ""

# Define paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate"
RESULTS_DIR="/fastscratch/tylerdoe/fusobacterium_results"
TREE_FILE="${RESULTS_DIR}/analysis/phylogenomics/prophage_tree.nwk"
METADATA_FILE="${PIPELINE_DIR}/fusobacterium_necrophorum_study/data/fusobacterium_metadata.tsv"
PROPHAGE_FILE="${PIPELINE_DIR}/fusobacterium_necrophorum_study/data/fusobacterium_metadata_prophage_merged.tsv"
OUTPUT_FILE="${PIPELINE_DIR}/fusobacterium_necrophorum_study/data/tree_sample_metadata_supplementary.tsv"

# Check files exist
if [ ! -f "${TREE_FILE}" ]; then
    echo "ERROR: Tree file not found: ${TREE_FILE}"
    exit 1
fi

if [ ! -f "${METADATA_FILE}" ]; then
    echo "ERROR: Metadata file not found: ${METADATA_FILE}"
    exit 1
fi

if [ ! -f "${PROPHAGE_FILE}" ]; then
    echo "ERROR: Prophage file not found: ${PROPHAGE_FILE}"
    exit 1
fi

echo "Input files:"
echo "  Tree: ${TREE_FILE}"
echo "  Metadata: ${METADATA_FILE}"
echo "  Prophage counts: ${PROPHAGE_FILE}"
echo ""
echo "Output file:"
echo "  ${OUTPUT_FILE}"
echo ""

# Run scripts
cd "${PIPELINE_DIR}"

echo "Creating comprehensive metadata table..."
echo ""
python3 fusobacterium_necrophorum_study/scripts/create_tree_metadata_table.py \
    "${TREE_FILE}" \
    "${METADATA_FILE}" \
    "${PROPHAGE_FILE}" \
    "${OUTPUT_FILE}"

echo ""
echo "Creating quick reference guide..."
echo ""
QUICK_REF="${PIPELINE_DIR}/fusobacterium_necrophorum_study/data/tree_quick_reference.txt"
python3 fusobacterium_necrophorum_study/scripts/create_tree_quick_reference.py \
    "${TREE_FILE}" \
    "${METADATA_FILE}" \
    "${QUICK_REF}"

echo ""
echo "========================================================================"
echo "Download files to local machine:"
echo "========================================================================"
echo ""
echo "# Full metadata table (for supplementary material):"
echo "scp tylerdoe@beocat.cis.ksu.edu:${OUTPUT_FILE} ."
echo ""
echo "# Quick reference (for viewing tree):"
echo "scp tylerdoe@beocat.cis.ksu.edu:${QUICK_REF} ."
echo ""
echo "This file contains:"
echo "  - Sample ID (SRR accession)"
echo "  - Subspecies (F. nucleatum, F. necrophorum, etc.)"
echo "  - Host species"
echo "  - Isolation source (oral, GI, blood, etc.)"
echo "  - Geographic location"
echo "  - Study details"
echo "  - Prophage count"
echo "  - Assembly information"
echo ""
echo "Use as:"
echo "  1. Supplementary Table for manuscript"
echo "  2. Reference for interpreting tree"
echo "  3. Lookup table: Which subspecies is SRR10901569?"
echo ""
