#!/bin/bash
#SBATCH --job-name=iqtree_subsample
#SBATCH --partition=ksu-gen-hi.q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=iqtree_subsample_%j.out
#SBATCH --error=iqtree_subsample_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

# Prophage Phylogenetic Tree Construction (Subsampled Data)
# Uses IQ-TREE for maximum likelihood tree with bootstrap support

echo "=========================================="
echo "Prophage Phylogeny - IQ-TREE (Subsample)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $HOSTNAME"
echo "Cores: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Start time: $(date)"
echo "=========================================="

# Set working directory
PHYLO_DIR="/bulk/tylerdoe/archives/compass_kansas_results/publication_analysis/phylogeny"
cd "$PHYLO_DIR"

echo "Working directory: $PHYLO_DIR"
echo ""

# Try to load IQ-TREE module (check which name works on Beocat)
# Try different possible module names
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
if [ ! -f "subsample_aligned.fasta" ]; then
    echo "❌ ERROR: subsample_aligned.fasta not found"
    echo "Please run alignment first: bash run_align_subsample.sh"
    exit 1
fi

# Count sequences
n_seqs=$(grep -c "^>" subsample_aligned.fasta)
echo "Number of sequences: $n_seqs"

# Check file size
file_size=$(du -h subsample_aligned.fasta | cut -f1)
echo "Alignment size: $file_size"

echo ""
echo "Starting IQ-TREE..."
echo "Expected runtime: 1-4 hours for $n_seqs sequences"

# Run IQ-TREE
# -s: input alignment
# -m MFP: ModelFinder Plus (automatically select best substitution model)
# -bb 1000: 1000 ultrafast bootstrap replicates
# -nt AUTO: auto-detect number of threads (will use $SLURM_CPUS_PER_TASK)
# -pre subsample_tree: prefix for output files

$IQTREE_CMD \
    -s subsample_aligned.fasta \
    -m MFP \
    -bb 1000 \
    -nt AUTO \
    -pre subsample_tree

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
    echo "  - subsample_tree.treefile (Newick format - USE THIS)"
    echo "  - subsample_tree.iqtree (Full report)"
    echo "  - subsample_tree.log (Log file)"
    echo "  - subsample_tree.bionj (Initial tree)"
    echo ""
    echo "Next steps:"
    echo "  1. Download subsample_tree.treefile to your computer"
    echo "  2. Visualize with iTOL (https://itol.embl.de/)"
    echo "  3. Upload subsample_metadata.tsv for annotation"
    echo ""
    echo "Or visualize with FigTree on Beocat:"
    echo "  module load FigTree"
    echo "  figtree subsample_tree.treefile"
    echo ""
    echo "To download files to your computer:"
    echo "  scp tylerdoe@beocat.cis.ksu.edu:$PHYLO_DIR/subsample_tree.treefile ."
    echo "  scp tylerdoe@beocat.cis.ksu.edu:$PHYLO_DIR/subsample_metadata.tsv ."
else
    echo "❌ ERROR: IQ-TREE failed with exit code $exit_code"
    echo "Check the log files for details"
fi

echo "=========================================="
