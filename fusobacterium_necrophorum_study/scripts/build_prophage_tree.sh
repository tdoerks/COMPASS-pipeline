#!/bin/bash
#
# Build phylogenetic tree of Fusobacterium prophages
#
# Requirements:
#   - MAFFT (alignment)
#   - FastTree (tree building)
#
# Usage: bash build_prophage_tree.sh
#

set -e

RESULTS_DIR="/fastscratch/tylerdoe/fusobacterium_results"
ANALYSIS_DIR="$RESULTS_DIR/analysis"
TREE_DIR="$ANALYSIS_DIR/phylogenomics"

echo "======================================================================"
echo "Fusobacterium Prophage Phylogenetic Tree Building"
echo "======================================================================"
echo ""

# Create tree directory
mkdir -p "$TREE_DIR"
cd "$TREE_DIR"

echo "Working directory: $(pwd)"
echo ""

# Step 1: Extract prophage sequences
echo "Step 1: Extracting prophage sequences..."
python3 /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/scripts/extract_prophage_sequences.py

if [ ! -f "$ANALYSIS_DIR/all_prophage_sequences.fna" ]; then
    echo "ERROR: Prophage sequences not found"
    exit 1
fi

# Copy to tree directory
cp "$ANALYSIS_DIR/all_prophage_sequences.fna" .

echo ""
echo "======================================================================"
echo "Step 2: Aligning prophage sequences with MAFFT"
echo "======================================================================"
echo ""

# Check if MAFFT is available
if ! command -v mafft &> /dev/null; then
    echo "ERROR: MAFFT not found"
    echo "Load module: module load MAFFT"
    echo "Or install: conda install -c bioconda mafft"
    exit 1
fi

echo "Running MAFFT alignment..."
echo "This may take 10-30 minutes for ~278 prophage sequences..."
echo ""

mafft --auto \
      --thread 8 \
      --adjustdirection \
      all_prophage_sequences.fna \
      > prophages_aligned.fna 2> mafft.log

echo "✓ Alignment complete"
echo ""

echo "======================================================================"
echo "Step 3: Building phylogenetic tree with FastTree"
echo "======================================================================"
echo ""

# Check if FastTree is available
if ! command -v FastTree &> /dev/null; then
    echo "ERROR: FastTree not found"
    echo "Load module: module load FastTree"
    echo "Or install: conda install -c bioconda fasttree"
    exit 1
fi

echo "Running FastTree..."
echo "This may take 5-15 minutes..."
echo ""

FastTree -nt -gtr \
         -log fasttree.log \
         prophages_aligned.fna \
         > prophage_tree.nwk

echo "✓ Tree building complete"
echo ""

echo "======================================================================"
echo "Results"
echo "======================================================================"
echo ""
echo "Files created:"
echo "  - all_prophage_sequences.fna     : Original prophage sequences"
echo "  - prophages_aligned.fna           : MAFFT alignment"
echo "  - prophage_tree.nwk               : Newick tree file"
echo "  - mafft.log                       : MAFFT log"
echo "  - fasttree.log                    : FastTree log"
echo ""
echo "Location: $TREE_DIR"
echo ""

# Get tree stats
n_seqs=$(grep -c "^>" all_prophage_sequences.fna)
echo "Prophage sequences in tree: $n_seqs"
echo ""

echo "======================================================================"
echo "Visualization Options"
echo "======================================================================"
echo ""
echo "1. Interactive Tree of Life (iTOL):"
echo "   - Upload prophage_tree.nwk to https://itol.embl.de/"
echo "   - Add metadata: subspecies, host, isolation source"
echo ""
echo "2. FigTree (local):"
echo "   - Download: http://tree.bio.ed.ac.uk/software/figtree/"
echo "   - Open prophage_tree.nwk"
echo ""
echo "3. R with ggtree:"
echo "   library(ggtree)"
echo "   tree <- read.tree('prophage_tree.nwk')"
echo "   ggtree(tree) + geom_tiplab(size=2)"
echo ""

echo "======================================================================"
echo "Analysis Questions"
echo "======================================================================"
echo ""
echo "Do prophages cluster by:"
echo "  1. Fusobacterium subspecies (vertical inheritance)?"
echo "  2. Prophage type (horizontal transfer)?"
echo "  3. Host species (human vs bovine)?"
echo "  4. Isolation source (oral vs gut)?"
echo ""
echo "Compare to host tree to determine:"
echo "  - Co-evolution vs horizontal gene transfer"
echo "  - F. necrophorum prophages: unique or shared?"
echo ""
echo "======================================================================"
echo "COMPLETE!"
echo "======================================================================"
