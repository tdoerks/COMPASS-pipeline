#!/bin/bash
#SBATCH --job-name=kansas_phylogeny
#SBATCH --partition=ksu-gen-hi.q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=iqtree_kansas_%j.out
#SBATCH --error=iqtree_kansas_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Kansas Prophage Phylogenetic Tree Construction
# Uses IQ-TREE for maximum likelihood tree with bootstrap support

echo "=========================================="
echo "Kansas Prophage Phylogeny - IQ-TREE"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $HOSTNAME"
echo "Cores: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Start time: $(date)"
echo "=========================================="

# Set working directory
PHYLO_DIR="/bulk/tylerdoe/archives/compass_kansas_results/phylogeny"
cd "$PHYLO_DIR"

echo "Working directory: $PHYLO_DIR"
echo ""

# Try to load IQ-TREE module (check which name works on Beocat)
if module load iqtree 2>/dev/null; then
    echo "✅ Loaded module: iqtree"
elif module load IQTREE 2>/dev/null; then
    echo "✅ Loaded module: IQTREE"
elif module load IQTree 2>/dev/null; then
    echo "✅ Loaded module: IQTree"
else
    echo "⚠️  No IQ-TREE module found, trying conda..."

    # Try to use conda
    if module load Anaconda3 2>/dev/null; then
        echo "✅ Loaded Anaconda3"

        # Check if phylo environment exists
        if conda env list | grep -q "^phylo "; then
            echo "✅ Activating existing phylo environment"
            source activate phylo
        else
            echo "Creating new phylo environment..."
            conda create -n phylo iqtree -c bioconda -y
            source activate phylo
        fi
    else
        echo "❌ ERROR: Could not load IQ-TREE or Anaconda3"
        echo "Please install IQ-TREE manually or contact Beocat support"
        exit 1
    fi
fi

# Verify IQ-TREE is available
if ! command -v iqtree2 &> /dev/null && ! command -v iqtree &> /dev/null; then
    echo "❌ ERROR: iqtree2/iqtree command not found"
    exit 1
fi

# Use iqtree2 if available, otherwise iqtree
if command -v iqtree2 &> /dev/null; then
    IQTREE_CMD="iqtree2"
else
    IQTREE_CMD="iqtree"
fi

echo "Using IQ-TREE command: $IQTREE_CMD"
$IQTREE_CMD --version
echo ""

echo "=========================================="
echo "Building Phylogenetic Tree"
echo "=========================================="

# Check if alignment exists
if [ ! -f "kansas_aligned.fasta" ]; then
    echo "❌ ERROR: kansas_aligned.fasta not found"
    echo "Please run alignment first:"
    echo "  bash run_align_kansas.sh"
    exit 1
fi

# Count sequences
n_seqs=$(grep -c "^>" kansas_aligned.fasta)
echo "Number of sequences: $n_seqs"

# Check file size
file_size=$(du -h kansas_aligned.fasta | cut -f1)
echo "Alignment size: $file_size"
echo ""

echo "Starting IQ-TREE..."
echo "Expected runtime: 1-4 hours for $n_seqs sequences"
echo ""

# Run IQ-TREE
# -s: input alignment
# -m MFP: ModelFinder Plus (automatically select best substitution model)
# -bb 1000: 1000 ultrafast bootstrap replicates
# -nt AUTO: auto-detect number of threads (will use $SLURM_CPUS_PER_TASK)
# -pre kansas_tree: prefix for output files

$IQTREE_CMD \
    -s kansas_aligned.fasta \
    -m MFP \
    -bb 1000 \
    -nt AUTO \
    -pre kansas_tree

exit_code=$?

echo ""
echo "=========================================="
echo "Job Complete"
echo "=========================================="
echo "Exit code: $exit_code"
echo "End time: $(date)"

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Phylogenetic tree constructed"
    echo ""
    echo "Output files:"
    echo "  - kansas_tree.treefile (Newick format - USE THIS)"
    echo "  - kansas_tree.iqtree (Full report with model selection)"
    echo "  - kansas_tree.log (Detailed log file)"
    echo "  - kansas_tree.bionj (Initial neighbor-joining tree)"
    echo ""
    echo "Tree statistics:"
    # Print some basic tree info from the .iqtree file
    if [ -f "kansas_tree.iqtree" ]; then
        echo "---"
        grep -A 2 "Best-fit model" kansas_tree.iqtree || true
        grep "Log-likelihood" kansas_tree.iqtree | head -1 || true
        echo "---"
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Download tree and metadata to your computer:"
    echo "     scp tylerdoe@beocat.cis.ksu.edu:$PHYLO_DIR/kansas_tree.treefile ."
    echo "     scp tylerdoe@beocat.cis.ksu.edu:$PHYLO_DIR/kansas_prophage_metadata.tsv ."
    echo ""
    echo "  2. Visualize with iTOL (https://itol.embl.de/):"
    echo "     - Upload kansas_tree.treefile"
    echo "     - Upload kansas_prophage_metadata.tsv as annotation"
    echo "     - Color by year and organism"
    echo ""
    echo "  3. Or use FigTree on Beocat:"
    echo "     module load FigTree"
    echo "     figtree kansas_tree.treefile"
    echo ""
    echo "  4. Generate publication figure with ggtree (R)"
    echo ""
else
    echo "❌ ERROR: IQ-TREE failed with exit code $exit_code"
    echo "Check the log files for details:"
    echo "  - kansas_tree.log"
    echo "  - iqtree_kansas_${SLURM_JOB_ID}.err"
fi

echo "=========================================="
