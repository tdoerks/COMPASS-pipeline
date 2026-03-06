#!/bin/bash
#SBATCH --job-name=iqtree_prophage
#SBATCH --partition=ksu-gen-hi.q
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=iqtree_%j.out
#SBATCH --error=iqtree_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tylerdoe@ksu.edu

# Prophage Phylogenetic Tree Construction
# Uses IQ-TREE for maximum likelihood tree with bootstrap support

echo "=========================================="
echo "Prophage Phylogeny - IQ-TREE"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $HOSTNAME"
echo "Cores: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "Start time: $(date)"
echo "=========================================="

# Set working directory
cd ~/compass_kansas_results/publication_analysis/phylogeny

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
if [ ! -f "prophages_aligned.fasta" ]; then
    echo "❌ ERROR: prophages_aligned.fasta not found"
    echo "Please run alignment first: mafft --auto --thread 16 complete_prophages.fasta > prophages_aligned.fasta"
    exit 1
fi

# Count sequences
n_seqs=$(grep -c "^>" prophages_aligned.fasta)
echo "Number of sequences: $n_seqs"

# Check file size
file_size=$(du -h prophages_aligned.fasta | cut -f1)
echo "Alignment size: $file_size"

echo ""
echo "Starting IQ-TREE..."
echo "This may take several hours for $n_seqs sequences..."

# Run IQ-TREE
# -s: input alignment
# -m MFP: ModelFinder Plus (automatically select best substitution model)
# -bb 1000: 1000 ultrafast bootstrap replicates
# -nt AUTO: auto-detect number of threads (will use $SLURM_CPUS_PER_TASK)
# -pre prophage_tree: prefix for output files

$IQTREE_CMD \
    -s prophages_aligned.fasta \
    -m MFP \
    -bb 1000 \
    -nt AUTO \
    -pre prophage_tree

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
    echo "  - prophage_tree.treefile (Newick format - USE THIS)"
    echo "  - prophage_tree.iqtree (Full report)"
    echo "  - prophage_tree.log (Log file)"
    echo "  - prophage_tree.bionj (Initial tree)"
    echo ""
    echo "Next steps:"
    echo "  1. Download prophage_tree.treefile to your computer"
    echo "  2. Visualize with iTOL (https://itol.embl.de/)"
    echo "  3. Upload prophage_metadata.tsv for annotation"
    echo ""
    echo "Or visualize with FigTree:"
    echo "  module load FigTree"
    echo "  figtree prophage_tree.treefile"
else
    echo "❌ ERROR: IQ-TREE failed with exit code $exit_code"
    echo "Check the log files for details"
fi

echo "=========================================="
