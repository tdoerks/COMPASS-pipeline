#!/bin/bash
#SBATCH --job-name=ecoli_amr_subsample_tree
#SBATCH --output=/homes/tylerdoe/slurm-ecoli-amr-subsample-tree-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-ecoli-amr-subsample-tree-%j.err
#SBATCH --time=168:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "E. coli AMR-Prophage Phylogeny"
echo "Subsampled Representative Dataset"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Find the most recent phylogeny directory
PHYLO_DIR=$(ls -td /homes/tylerdoe/ecoli_amr_prophage_phylogeny_* 2>/dev/null | head -1)

if [ -z "$PHYLO_DIR" ]; then
    echo "❌ ERROR: No E. coli AMR-prophage phylogeny directory found"
    exit 1
fi

echo "Using phylogeny directory: $PHYLO_DIR"
echo ""

# Check if extracted sequences exist
AMR_PROPHAGE_FASTA="$PHYLO_DIR/amr_prophages.fasta"
AMR_PROPHAGE_METADATA="$PHYLO_DIR/amr_prophage_metadata.tsv"

if [ ! -f "$AMR_PROPHAGE_FASTA" ]; then
    echo "❌ ERROR: AMR prophage sequences not found: $AMR_PROPHAGE_FASTA"
    echo "   You need to run the full script first to extract sequences"
    exit 1
fi

if [ ! -f "$AMR_PROPHAGE_METADATA" ]; then
    echo "❌ ERROR: AMR prophage metadata not found: $AMR_PROPHAGE_METADATA"
    exit 1
fi

NUM_SEQS=$(grep -c "^>" "$AMR_PROPHAGE_FASTA")
echo "✅ Found extracted sequences: $NUM_SEQS AMR-carrying prophages"
echo ""

# Load required modules
echo "Loading required modules..."
module load Biopython/1.79-foss-2022a || echo "⚠️  Biopython module not found"
module load MAFFT || echo "⚠️  MAFFT module not found"
module load FastTree/2.1.11-GCCcore-11.3.0 || echo "⚠️  FastTree module not found"

# Verify Python can import Bio
echo ""
echo "Verifying BioPython installation..."
python3 -c "from Bio import SeqIO; print('✅ BioPython import successful')" || {
    echo "❌ ERROR: BioPython module loaded but Python cannot import it"
    exit 1
}

# Check if tools are available
echo ""
echo "Checking required tools..."
which mafft > /dev/null 2>&1 && echo "✅ MAFFT found" || { echo "❌ MAFFT not found"; exit 1; }
which FastTree > /dev/null 2>&1 && echo "✅ FastTree found" || { echo "❌ FastTree not found"; exit 1; }
echo ""

# Pipeline directory (hardcoded since SLURM changes working directory)
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
SUBSAMPLE_SCRIPT="$PIPELINE_DIR/bin/subsample_ecoli_amr_prophages.py"

if [ ! -f "$SUBSAMPLE_SCRIPT" ]; then
    echo "❌ ERROR: Subsampling script not found: $SUBSAMPLE_SCRIPT"
    echo "   Make sure you're running from: $PIPELINE_DIR"
    echo "   And that you've pulled the latest v1.3-dev branch"
    exit 1
fi

echo "✅ Subsampling script found: $SUBSAMPLE_SCRIPT"
echo ""

# ============================================================================
# STEP 1: Subsample to Representative Dataset
# ============================================================================

echo "=========================================="
echo "STEP 1: Subsample to Representative Set"
echo "=========================================="
echo ""

SUBSAMPLE_FASTA="$PHYLO_DIR/amr_prophages_subsample.fasta"
SUBSAMPLE_METADATA="$PHYLO_DIR/amr_prophage_subsample_metadata.tsv"

echo "Subsampling strategy: 100 prophages per year (2021-2024)"
echo "Expected total: ~400 prophages (down from $NUM_SEQS)"
echo ""
echo "Selection criteria:"
echo "  - Balanced representation across 2021-2024"
echo "  - Longest prophages per year (proxy for completeness)"
echo "  - Reproducible random seed (42)"
echo ""

python3 "$SUBSAMPLE_SCRIPT" \
    --strategy by_year \
    --n-per-year 100 \
    --input-fasta "$AMR_PROPHAGE_FASTA" \
    --input-metadata "$AMR_PROPHAGE_METADATA" \
    --output-fasta "$SUBSAMPLE_FASTA" \
    --output-metadata "$SUBSAMPLE_METADATA"

STEP1_EXIT=$?

if [ $STEP1_EXIT -ne 0 ]; then
    echo ""
    echo "❌ STEP 1 FAILED: Could not subsample AMR-prophages"
    exit 1
fi

if [ ! -f "$SUBSAMPLE_FASTA" ]; then
    echo "❌ ERROR: Subsample FASTA file not created"
    exit 1
fi

NUM_SUBSAMPLE=$(grep -c "^>" "$SUBSAMPLE_FASTA")

echo ""
echo "✅ STEP 1 COMPLETE"
echo "   Original: $NUM_SEQS prophages"
echo "   Subsampled: $NUM_SUBSAMPLE prophages ($(echo "scale=1; $NUM_SUBSAMPLE * 100 / $NUM_SEQS" | bc)% of original)"
echo ""

# ============================================================================
# STEP 2: Multiple Sequence Alignment with MAFFT
# ============================================================================

echo "=========================================="
echo "STEP 2: Multiple Sequence Alignment"
echo "=========================================="
echo ""

ALIGNED_FASTA="$PHYLO_DIR/amr_prophages_subsample_aligned.fasta"

# Backup old alignment if it exists
if [ -f "$ALIGNED_FASTA" ]; then
    echo "⚠️  Old alignment file exists, backing up..."
    mv "$ALIGNED_FASTA" "${ALIGNED_FASTA}.old"
    echo "   Backup: ${ALIGNED_FASTA}.old"
fi

echo "Running MAFFT alignment on $NUM_SUBSAMPLE AMR-carrying prophages..."
echo "Output: $ALIGNED_FASTA"
echo ""
echo "⏱️  Estimated time: 2-5 hours for $NUM_SUBSAMPLE sequences"
echo ""

START_TIME=$(date +%s)

mafft \
    --auto \
    --thread $SLURM_CPUS_PER_TASK \
    "$SUBSAMPLE_FASTA" \
    > "$ALIGNED_FASTA" 2> >(tee "$PHYLO_DIR/mafft_subsample.log" >&2)

MAFFT_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

echo ""
if [ $MAFFT_EXIT -eq 0 ] && [ -s "$ALIGNED_FASTA" ]; then
    echo "✅ MAFFT alignment completed in ${HOURS}h ${MINUTES}m"

    # Verify it's a real FASTA file (starts with >)
    FIRST_CHAR=$(head -c 1 "$ALIGNED_FASTA")
    if [ "$FIRST_CHAR" = ">" ]; then
        echo "✅ Alignment file looks valid (starts with '>')"
    else
        echo "❌ ERROR: Alignment file doesn't look like FASTA (doesn't start with '>')"
        echo "   First 100 characters:"
        head -c 100 "$ALIGNED_FASTA"
        echo ""
        exit 1
    fi
else
    echo "❌ MAFFT alignment failed"
    exit 1
fi

echo ""

# ============================================================================
# STEP 3: Phylogenetic Tree Construction with FastTree
# ============================================================================

echo "=========================================="
echo "STEP 3: Phylogenetic Tree Construction"
echo "=========================================="
echo ""

TREE_FILE="$PHYLO_DIR/amr_prophage_subsample_tree.nwk"

# Backup old tree if it exists
if [ -f "$TREE_FILE" ]; then
    echo "⚠️  Old tree file exists, backing up..."
    mv "$TREE_FILE" "${TREE_FILE}.old"
    echo "   Backup: ${TREE_FILE}.old"
fi

echo "Running FastTree on $NUM_SUBSAMPLE AMR-carrying prophages..."
echo "Output: $TREE_FILE"
echo "Model: GTR + Gamma"
echo "Bootstrap replicates: 1000"
echo ""
echo "⏱️  Estimated time: 30-60 minutes for $NUM_SUBSAMPLE sequences"
echo ""

START_TIME=$(date +%s)

FastTree -nt -gtr -gamma -boot 1000 "$ALIGNED_FASTA" > "$TREE_FILE" 2>&1

FASTTREE_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))

echo ""
if [ $FASTTREE_EXIT -eq 0 ] && [ -s "$TREE_FILE" ]; then
    TREE_SIZE=$(stat -c%s "$TREE_FILE" 2>/dev/null || stat -f%z "$TREE_FILE")
    echo "✅ FastTree completed in ${MINUTES} minutes"
    echo "   Tree file size: $((TREE_SIZE / 1024)) KB"

    # Check if tree looks valid (should contain parentheses and be >1KB)
    if [ $TREE_SIZE -lt 1000 ]; then
        echo "⚠️  WARNING: Tree file is very small (<1KB), may contain only error messages"
        echo "   First 500 characters:"
        head -c 500 "$TREE_FILE"
        echo ""
    fi
else
    echo "❌ FastTree failed"
    exit 1
fi

echo ""

# ============================================================================
# STEP 4: Clean Tree (Remove Colons from Sequence IDs)
# ============================================================================

echo "=========================================="
echo "STEP 4: Clean Tree Format"
echo "=========================================="
echo ""

CLEANED_TREE="$PHYLO_DIR/amr_prophage_subsample_tree_cleaned.nwk"

echo "Fixing Newick format (removing colons from sequence IDs)..."
echo ""

# Extract just the tree line (last line, should start with parenthesis)
tail -1 "$TREE_FILE" > "$PHYLO_DIR/amr_prophage_subsample_tree_only.nwk"

# Replace all colons with underscores
sed 's/:/_/g' "$PHYLO_DIR/amr_prophage_subsample_tree_only.nwk" > "$PHYLO_DIR/temp_tree.nwk"

# Restore colons only before branch lengths (numbers followed by delimiters)
sed -E 's/_([0-9]+\.[0-9]+)([,);])/:\1\2/g' "$PHYLO_DIR/temp_tree.nwk" > "$CLEANED_TREE"

# Clean up temp files
rm -f "$PHYLO_DIR/temp_tree.nwk" "$PHYLO_DIR/amr_prophage_subsample_tree_only.nwk"

if [ -f "$CLEANED_TREE" ] && [ -s "$CLEANED_TREE" ]; then
    CLEANED_SIZE=$(stat -c%s "$CLEANED_TREE" 2>/dev/null || stat -f%z "$CLEANED_TREE")
    echo "✅ Created cleaned tree: $CLEANED_TREE"
    echo "   Size: $((CLEANED_SIZE / 1024)) KB"
    echo ""
    echo "First 300 characters:"
    head -c 300 "$CLEANED_TREE"
    echo ""
else
    echo "❌ ERROR: Failed to create cleaned tree"
    exit 1
fi

echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo "=========================================="
echo "🎉 SUBSAMPLED PHYLOGENY COMPLETE!"
echo "=========================================="
echo ""
echo "End time: $(date)"
echo ""
echo "📁 Output Directory: $PHYLO_DIR"
echo ""
echo "📊 Output Files:"
echo "   - amr_prophage_subsample_tree_cleaned.nwk (ready for iTOL)"
echo "   - amr_prophage_subsample_tree.nwk (original with FastTree logs)"
echo "   - amr_prophages_subsample_aligned.fasta (alignment)"
echo "   - amr_prophages_subsample.fasta (subsampled sequences)"
echo "   - amr_prophage_subsample_metadata.tsv (metadata)"
echo ""
echo "📈 Dataset Summary:"
echo "   - Original prophages: $NUM_SEQS"
echo "   - Subsampled prophages: $NUM_SUBSAMPLE"
echo "   - Reduction: $(echo "scale=1; ($NUM_SEQS - $NUM_SUBSAMPLE) * 100 / $NUM_SEQS" | bc)%"
echo "   - Years: 2021-2024 (~100 prophages per year)"
echo ""
echo "🌳 Download Tree:"
echo "   scp tylerdoe@beocat.ksu.edu:$CLEANED_TREE ."
echo "   scp tylerdoe@beocat.ksu.edu:$SUBSAMPLE_METADATA ."
echo ""
echo "📈 Upload to iTOL:"
echo "   https://itol.embl.de/"
echo ""
echo "🔬 Key Questions:"
echo "   1. Do AMR-carrying prophages cluster by year (2021-2024)?"
echo "   2. Are there AMR-prophage lineages?"
echo "   3. Which prophage clades carry more AMR genes?"
echo ""
echo "✅ Benefits of Subsampling:"
echo "   - Faster alignment (2-5 hrs vs 55-60 hrs)"
echo "   - Fits in 32GB memory (vs OOM failure)"
echo "   - Easier tree visualization in iTOL"
echo "   - Representative temporal diversity preserved"
echo ""
echo "=========================================="

exit 0
