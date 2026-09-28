#!/bin/bash
#
# Build phylogenetic tree of Fusobacterium host genomes
# For comparison to prophage tree
#
# Strategy: Use BUSCO single-copy genes as core genome markers
#

set -e

RESULTS_DIR="/fastscratch/tylerdoe/fusobacterium_results"
ANALYSIS_DIR="$RESULTS_DIR/analysis"
TREE_DIR="$ANALYSIS_DIR/phylogenomics"

echo "======================================================================"
echo "Fusobacterium Host Genome Phylogenetic Tree"
echo "======================================================================"
echo ""

mkdir -p "$TREE_DIR"
cd "$TREE_DIR"

echo "Working directory: $(pwd)"
echo ""

echo "======================================================================"
echo "Strategy: Extract BUSCO Single-Copy Genes"
echo "======================================================================"
echo ""
echo "BUSCO identified conserved bacterial genes in each genome"
echo "We'll use these as 'core genes' for phylogenetic analysis"
echo ""

# Find all BUSCO results
BUSCO_DIR="$RESULTS_DIR/busco"

echo "Step 1: Extracting BUSCO single-copy genes..."
echo ""

# Count samples with BUSCO results
n_samples=$(ls -1 "$BUSCO_DIR" | grep "_busco$" | wc -l)
echo "Samples with BUSCO results: $n_samples"
echo ""

# Create directory for concatenated genes
mkdir -p busco_genes

# For each sample, extract a few highly conserved BUSCO genes
echo "Extracting conserved genes from BUSCO results..."
echo "(This is a simplified approach - full analysis would use all single-copy genes)"
echo ""

# Create gene list file
gene_count=0

for sample_dir in "$BUSCO_DIR"/SRR*_busco; do
    sample=$(basename "$sample_dir" | sed 's/_busco$//')

    # Find BUSCO sequences directory
    seq_dir="$sample_dir/auto_lineage/run_bacteria_odb10/busco_sequences/single_copy_busco_sequences"

    if [ -d "$seq_dir" ]; then
        # Count genes
        n_genes=$(ls -1 "$seq_dir"/*.faa 2>/dev/null | wc -l)
        if [ $n_genes -gt 0 ]; then
            echo "$sample: $n_genes single-copy genes"
            gene_count=$((gene_count + 1))
        fi
    fi
done | head -20

echo ""
echo "Samples with single-copy BUSCO genes: $gene_count"
echo ""

echo "======================================================================"
echo "Alternative: 16S rRNA Tree (Simpler)"
echo "======================================================================"
echo ""
echo "For a quick host tree, we can use 16S rRNA sequences"
echo "These can be extracted from assemblies using barrnap or infernal"
echo ""
echo "Commands:"
echo "  1. Extract 16S from assemblies:"
echo "     for assembly in assemblies/*.fasta; do"
echo "       barrnap --kingdom bac \$assembly > 16S/\$(basename \$assembly .fasta)_16S.gff"
echo "     done"
echo ""
echo "  2. Extract sequences from GFF"
echo "  3. Align with MAFFT"
echo "  4. Build tree with FastTree"
echo ""

echo "======================================================================"
echo "Full Core Genome Approach (Most Accurate)"
echo "======================================================================"
echo ""
echo "For publication-quality tree:"
echo ""
echo "Option 1: Use existing tool like Roary or PIRATE"
echo "  - Identifies core genes across all genomes"
echo "  - Concatenates alignments"
echo "  - Builds ML tree"
echo ""
echo "Option 2: Use BUSCO genes (implemented here)"
echo "  1. Extract all single-copy BUSCO genes"
echo "  2. For each BUSCO gene:"
echo "     - Collect sequences from all samples"
echo "     - Align with MAFFT"
echo "  3. Concatenate alignments"
echo "  4. Build tree with RAxML or IQ-TREE"
echo ""

echo "======================================================================"
echo "Recommended Quick Approach"
echo "======================================================================"
echo ""
echo "For Fusobacterium prophage analysis, simplest approach:"
echo ""
echo "1. Use metadata to group samples:"
echo "   - F. nucleatum, F. necrophorum, F. funduliforme, etc."
echo "   - Human vs bovine hosts"
echo "   - Oral vs GI tract"
echo ""
echo "2. Compare prophage tree branches to these groupings"
echo ""
echo "3. Ask:"
echo "   - Do F. necrophorum prophages cluster together?"
echo "   - Do bovine isolate prophages cluster (regardless of subspecies)?"
echo "   - Do oral isolate prophages cluster?"
echo ""
echo "If prophages cluster by SUBSPECIES → Vertical inheritance"
echo "If prophages cluster by PROPHAGE TYPE → Horizontal transfer"
echo ""

echo "======================================================================"
echo "Simple Implementation: Metadata-based Comparison"
echo "======================================================================"
echo ""

# Create sample-subspecies mapping
echo "Creating metadata mapping for tree annotation..."
echo ""

# Read metadata
METADATA="$RESULTS_DIR/../COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/fusobacterium_metadata.tsv"

if [ -f "$METADATA" ]; then
    echo "Sample,Subspecies,Host" > sample_metadata.csv

    tail -n +2 "$METADATA" | cut -f8,82,40 | head -20 | \
    awk -F'\t' '{print $1 "," $2 "," $3}' >> sample_metadata.csv

    echo "✓ Created sample_metadata.csv"
    echo ""
    echo "Use this to annotate your prophage tree in iTOL:"
    echo "  1. Upload prophage_tree.nwk to iTOL"
    echo "  2. Upload sample_metadata.csv as annotation"
    echo "  3. Color branches by subspecies or host"
    echo ""
else
    echo "Metadata file not found: $METADATA"
fi

echo "======================================================================"
echo "Summary"
echo "======================================================================"
echo ""
echo "For Fusobacterium prophage analysis:"
echo ""
echo "RECOMMENDED APPROACH:"
echo "  1. Build prophage tree (see build_prophage_tree.sh)"
echo "  2. Annotate with metadata (subspecies, host, source)"
echo "  3. Look for clustering patterns"
echo "  4. No need for full host tree initially"
echo ""
echo "IF YOU NEED HOST TREE:"
echo "  - Use 16S rRNA (quick, ~1 hour)"
echo "  - Or BUSCO core genes (accurate, ~1 day)"
echo "  - Or wait for publication - can use existing Fusobacterium phylogeny"
echo ""
echo "======================================================================"
