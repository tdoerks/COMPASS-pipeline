#!/bin/bash
#SBATCH --job-name=prophage_phylogeny
#SBATCH --output=/homes/tylerdoe/slurm-prophage-phylo-%j.out
#SBATCH --error=/homes/tylerdoe/slurm-prophage-phylo-%j.err
#SBATCH --time=48:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=tdoerks@vet.k-state.edu

echo "=========================================="
echo "Complete Prophage Phylogenetic Analysis"
echo "Kansas 2021-2025 NARMS Dataset"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Start time: $(date)"
echo ""

# Set paths
PIPELINE_DIR="/fastscratch/tylerdoe/COMPASS-pipeline"
RESULTS_DIR="/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod"
OUTPUT_DIR="/homes/tylerdoe/prophage_phylogeny_$(date +%Y%m%d)"

# Create output directory
mkdir -p "$OUTPUT_DIR"
cd "$PIPELINE_DIR" || exit 1

echo "Pipeline directory: $PIPELINE_DIR"
echo "Results directory: $RESULTS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Load required modules
echo "Loading required modules..."
module load MAFFT || echo "⚠️  MAFFT module not found, trying system install"
module load Biopython/1.79-foss-2022a || echo "⚠️  Biopython module not found"
module load IQ-TREE || echo "⚠️  IQ-TREE module not found, trying system install"

# Verify Python can import Bio
echo ""
echo "Verifying BioPython installation..."
python3 -c "from Bio import SeqIO; print('✅ BioPython import successful')" || {
    echo "❌ ERROR: BioPython module loaded but Python cannot import it"
    echo "   This may be a PYTHONPATH issue"
    exit 1
}

# Check if tools are available
echo ""
echo "Checking required tools..."
which mafft > /dev/null 2>&1 && echo "✅ MAFFT found: $(which mafft)" || echo "❌ MAFFT not found"
which iqtree > /dev/null 2>&1 && echo "✅ IQ-TREE found: $(which iqtree)" || echo "❌ IQ-TREE not found"
which iqtree2 > /dev/null 2>&1 && echo "✅ IQ-TREE2 found: $(which iqtree2)" || echo "❌ IQ-TREE2 not found"
which python3 > /dev/null 2>&1 && echo "✅ Python3 found: $(which python3)" || echo "❌ Python3 not found"

# Determine which IQ-TREE version is available
if which iqtree2 > /dev/null 2>&1; then
    IQTREE_CMD="iqtree2"
elif which iqtree > /dev/null 2>&1; then
    IQTREE_CMD="iqtree"
else
    IQTREE_CMD=""
fi

echo ""

# ============================================================================
# STEP 1: Extract Prophage Sequences
# ============================================================================

echo "=========================================="
echo "STEP 1: Extracting Prophage Sequences"
echo "=========================================="
echo ""

PROPHAGE_FASTA="$OUTPUT_DIR/prophages_all.fasta"
PROPHAGE_METADATA="$OUTPUT_DIR/prophage_metadata.tsv"

echo "Extracting prophage sequences from VIBRANT output..."
echo "This will create a multi-FASTA file with all prophage sequences."
echo ""

# Create Python script inline to extract prophages
python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
from Bio import SeqIO
import csv

results_dir = Path("/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod")
vibrant_dir = results_dir / "vibrant"
output_fasta = Path("/homes/tylerdoe/prophage_phylogeny_$(date +%Y%m%d)/prophages_all.fasta").parent / "prophages_all.fasta"
output_metadata = output_fasta.parent / "prophage_metadata.tsv"

print(f"Scanning VIBRANT directory: {vibrant_dir}")
print(f"Output FASTA: {output_fasta}")

sequences = []
metadata_rows = []

# Find all prophage FASTA files
phage_files = list(vibrant_dir.glob("*_phages.fna"))
print(f"Found {len(phage_files)} samples with prophage data")

for i, phage_file in enumerate(sorted(phage_files), 1):
    sample_id = phage_file.stem.replace('_phages', '')

    if i % 100 == 0:
        print(f"  Processed {i}/{len(phage_files)} samples...")

    try:
        for record in SeqIO.parse(phage_file, "fasta"):
            # Rename sequence ID to include sample
            orig_id = record.id
            record.id = f"{sample_id}_{orig_id}"
            record.description = f"sample={sample_id} length={len(record.seq)}"

            sequences.append(record)

            # Store metadata
            metadata_rows.append({
                'prophage_id': record.id,
                'sample_id': sample_id,
                'length_bp': len(record.seq),
                'original_id': orig_id
            })
    except Exception as e:
        print(f"  ⚠️  Error processing {phage_file.name}: {e}")

print(f"\n✅ Extracted {len(sequences)} prophage sequences from {len(phage_files)} samples")

# Write FASTA
SeqIO.write(sequences, output_fasta, "fasta")
print(f"✅ Saved sequences to: {output_fasta}")

# Write metadata
with open(output_metadata, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['prophage_id', 'sample_id', 'length_bp', 'original_id'], delimiter='\t')
    writer.writeheader()
    writer.writerows(metadata_rows)

print(f"✅ Saved metadata to: {output_metadata}")
print(f"\nTotal sequences: {len(sequences)}")
print(f"Total size: {sum(len(s.seq) for s in sequences):,} bp")

# Calculate size statistics
lengths = [len(s.seq) for s in sequences]
if lengths:
    import statistics
    print(f"Length range: {min(lengths):,} - {max(lengths):,} bp")
    print(f"Mean length: {statistics.mean(lengths):,.0f} bp")
    print(f"Median length: {statistics.median(lengths):,.0f} bp")

PYTHON_SCRIPT

STEP1_EXIT=$?

if [ $STEP1_EXIT -ne 0 ]; then
    echo ""
    echo "❌ STEP 1 FAILED: Could not extract prophage sequences"
    echo "Check error messages above"
    exit 1
fi

# Update paths with actual date
PROPHAGE_FASTA=$(ls "$OUTPUT_DIR"/prophages_all.fasta 2>/dev/null | head -1)
PROPHAGE_METADATA=$(ls "$OUTPUT_DIR"/prophage_metadata.tsv 2>/dev/null | head -1)

if [ ! -f "$PROPHAGE_FASTA" ]; then
    echo "❌ ERROR: Prophage FASTA file not created"
    exit 1
fi

NUM_SEQS=$(grep -c "^>" "$PROPHAGE_FASTA")
TOTAL_SIZE=$(stat -f%z "$PROPHAGE_FASTA" 2>/dev/null || stat -c%s "$PROPHAGE_FASTA")

echo ""
echo "✅ STEP 1 COMPLETE"
echo "   Sequences: $NUM_SEQS"
echo "   FASTA size: $((TOTAL_SIZE / 1024 / 1024)) MB"
echo ""

# ============================================================================
# STEP 2: Subsample if Too Many Sequences
# ============================================================================

echo "=========================================="
echo "STEP 2: Subsample (if needed)"
echo "=========================================="
echo ""

MAX_SEQS=500  # Maximum sequences for reasonable phylogeny runtime

if [ "$NUM_SEQS" -gt "$MAX_SEQS" ]; then
    echo "⚠️  Dataset has $NUM_SEQS sequences (> $MAX_SEQS)"
    echo "   Subsampling to $MAX_SEQS sequences for manageable runtime..."
    echo ""

    SUBSAMPLED_FASTA="$OUTPUT_DIR/prophages_subsampled.fasta"

    # Subsample using seqtk (if available) or Python
    if which seqtk > /dev/null 2>&1; then
        # Calculate subsample proportion
        PROPORTION=$(awk "BEGIN {print $MAX_SEQS/$NUM_SEQS}")
        seqtk sample -s100 "$PROPHAGE_FASTA" "$PROPORTION" > "$SUBSAMPLED_FASTA"
        echo "✅ Subsampled using seqtk"
    else
        # Python-based subsampling
        python3 << PYCODE
from Bio import SeqIO
import random

random.seed(42)
records = list(SeqIO.parse("$PROPHAGE_FASTA", "fasta"))
sampled = random.sample(records, min($MAX_SEQS, len(records)))
SeqIO.write(sampled, "$SUBSAMPLED_FASTA", "fasta")
print(f"✅ Subsampled {len(sampled)} sequences")
PYCODE
    fi

    ALIGNMENT_INPUT="$SUBSAMPLED_FASTA"
    NUM_SEQS=$MAX_SEQS
    echo "   Using subsampled FASTA for alignment: $ALIGNMENT_INPUT"
else
    echo "✅ Dataset size OK ($NUM_SEQS sequences ≤ $MAX_SEQS)"
    echo "   Using full dataset for alignment"
    ALIGNMENT_INPUT="$PROPHAGE_FASTA"
fi

echo ""

# ============================================================================
# STEP 3: Multiple Sequence Alignment with MAFFT
# ============================================================================

echo "=========================================="
echo "STEP 3: Multiple Sequence Alignment"
echo "=========================================="
echo ""

ALIGNED_FASTA="$OUTPUT_DIR/prophages_aligned.fasta"

if ! which mafft > /dev/null 2>&1; then
    echo "❌ ERROR: MAFFT not found"
    echo "   Cannot perform alignment without MAFFT"
    echo ""
    echo "   To install MAFFT on Beocat:"
    echo "     module load MAFFT"
    echo "   Or:"
    echo "     conda install -c bioconda mafft"
    exit 1
fi

echo "Running MAFFT alignment..."
echo "Input: $ALIGNMENT_INPUT ($NUM_SEQS sequences)"
echo "Output: $ALIGNED_FASTA"
echo ""
echo "This may take 30-60 minutes depending on dataset size..."
echo ""

START_TIME=$(date +%s)

mafft \
    --auto \
    --thread $SLURM_CPUS_PER_TASK \
    "$ALIGNMENT_INPUT" \
    > "$ALIGNED_FASTA" 2>&1 | tee "$OUTPUT_DIR/mafft.log"

MAFFT_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))

echo ""
if [ $MAFFT_EXIT -eq 0 ] && [ -s "$ALIGNED_FASTA" ]; then
    echo "✅ MAFFT alignment completed in ${MINUTES} minutes"
    ALIGNED_SIZE=$(stat -f%z "$ALIGNED_FASTA" 2>/dev/null || stat -c%s "$ALIGNED_FASTA")
    echo "   Aligned FASTA size: $((ALIGNED_SIZE / 1024 / 1024)) MB"
else
    echo "❌ MAFFT alignment failed"
    echo "Check log: $OUTPUT_DIR/mafft.log"
    exit 1
fi

echo ""

# ============================================================================
# STEP 4: Phylogenetic Tree Construction with IQ-TREE
# ============================================================================

echo "=========================================="
echo "STEP 4: Phylogenetic Tree Construction"
echo "=========================================="
echo ""

if [ -z "$IQTREE_CMD" ]; then
    echo "❌ ERROR: IQ-TREE not found"
    echo "   Cannot build tree without IQ-TREE"
    echo ""
    echo "   To install IQ-TREE on Beocat:"
    echo "     module load IQ-TREE"
    echo "   Or:"
    echo "     conda install -c bioconda iqtree"
    echo ""
    echo "✅ Alignment completed successfully!"
    echo "   You can build the tree manually:"
    echo "   iqtree2 -s $ALIGNED_FASTA -m MFP -bb 1000 -nt $SLURM_CPUS_PER_TASK"
    exit 0
fi

echo "Running IQ-TREE phylogenetic analysis..."
echo "Command: $IQTREE_CMD"
echo "Input: $ALIGNED_FASTA"
echo "Threads: $SLURM_CPUS_PER_TASK"
echo "Bootstrap replicates: 1000"
echo ""
echo "This may take 1-4 hours depending on dataset size..."
echo ""

START_TIME=$(date +%s)

cd "$OUTPUT_DIR" || exit 1

$IQTREE_CMD \
    -s "$(basename "$ALIGNED_FASTA")" \
    -m MFP \
    -bb 1000 \
    -nt $SLURM_CPUS_PER_TASK \
    -pre prophage_tree

IQTREE_EXIT=$?
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

echo ""
if [ $IQTREE_EXIT -eq 0 ]; then
    echo "✅ IQ-TREE completed in ${HOURS}h ${MINUTES}m"
    echo ""
    echo "Output files:"
    ls -lh prophage_tree.* 2>/dev/null
else
    echo "❌ IQ-TREE failed"
    echo "Check log: prophage_tree.log"
    exit 1
fi

echo ""

# ============================================================================
# STEP 5: Generate Visualization Guide
# ============================================================================

echo "=========================================="
echo "STEP 5: Generate Visualization Guide"
echo "=========================================="
echo ""

GUIDE_FILE="$OUTPUT_DIR/VISUALIZATION_GUIDE.md"

cat > "$GUIDE_FILE" << 'EOF'
# Prophage Phylogenetic Tree - Visualization Guide

## Files Generated

### Tree Files
- `prophage_tree.treefile` - Best-scoring Maximum Likelihood tree (Newick format)
- `prophage_tree.contree` - Consensus tree with bootstrap support values
- `prophage_tree.iqtree` - Full IQ-TREE report with model selection and statistics

### Alignment Files
- `prophages_aligned.fasta` - Multiple sequence alignment (MAFFT)
- `prophages_all.fasta` or `prophages_subsampled.fasta` - Original sequences

### Metadata
- `prophage_metadata.tsv` - Sample metadata for tree annotation

## Quick Visualization Options

### Option 1: iTOL (Recommended - Interactive Online Tool)

1. Go to https://itol.embl.de/
2. Click "Upload" and select `prophage_tree.treefile`
3. Upload `prophage_metadata.tsv` as a dataset (use sample_id as label)
4. Customize:
   - Color by sample year
   - Add sample labels
   - Show bootstrap support (values >70 indicate strong support)
5. Export as SVG for publication

**Benefits**: Interactive, beautiful, publication-ready

### Option 2: FigTree (Desktop Application)

```bash
# Download from: http://tree.bio.ed.ac.uk/software/figtree/
figtree prophage_tree.treefile
```

**Benefits**: Local, no internet needed, good for exploration

### Option 3: R with ggtree (Programmable)

```R
library(ggtree)
library(ggplot2)
library(dplyr)

# Load tree
tree <- read.tree("prophage_tree.treefile")

# Load metadata
metadata <- read.table("prophage_metadata.tsv",
                       header=TRUE,
                       sep="\t",
                       stringsAsFactors=FALSE)

# Basic tree
p <- ggtree(tree) %<+% metadata +
  geom_tippoint(aes(color=sample_id), size=2) +
  geom_tiplab(size=2, align=TRUE) +
  theme_tree2() +
  labs(title="Prophage Phylogenetic Tree",
       subtitle="Kansas NARMS 2021-2025")

ggsave("prophage_tree.pdf", p, width=12, height=10)
```

**Benefits**: Reproducible, scriptable, publication-ready

### Option 4: Python with ETE3

```python
from ete3 import Tree, TreeStyle, TextFace

# Load tree
t = Tree("prophage_tree.treefile")

# Set up style
ts = TreeStyle()
ts.show_leaf_name = True
ts.show_branch_support = True

# Render
t.render("prophage_tree.png", tree_style=ts, w=1200, units="px")
```

## Interpreting the Tree

### Bootstrap Support Values
- **>90%**: Very strong support - high confidence
- **70-90%**: Strong support - good confidence
- **50-70%**: Moderate support - interpret cautiously
- **<50%**: Weak support - unreliable branching

### Key Questions to Explore

1. **Temporal Clustering**: Do prophages from the same year cluster together?
   - If YES → Prophages are evolving/spreading rapidly
   - If NO → Prophages are stable over time

2. **Host Specificity**: Do prophages cluster by bacterial host species?
   - If YES → Prophages are host-specific
   - If NO → Prophages can infect multiple species

3. **Geographic Patterns**: Do prophages from same locations cluster?
   - Requires geo metadata to test

4. **AMR Association**: Do prophages carrying AMR genes cluster?
   - Can integrate with AMR analysis results

## Advanced Analysis

### Root the Tree

If you have an outgroup sequence, root the tree:

```R
# In R with ape
library(ape)
tree <- read.tree("prophage_tree.treefile")
rooted_tree <- root(tree, outgroup="OUTGROUP_ID")
write.tree(rooted_tree, "prophage_tree_rooted.nwk")
```

### Test for Temporal Signal

Check if branch lengths correlate with sampling time:

```R
library(ape)
library(phytools)

tree <- read.tree("prophage_tree.treefile")
# Run root-to-tip regression
# Positive correlation = temporal signal present
```

### Compare to Reference Prophage Database

Use BLAST to identify your prophages against known databases:
- PHASTER database
- IMG/VR database
- RefSeq viral genomes

## Troubleshooting

**Tree looks like a star (no resolution)**
- Not enough phylogenetic signal
- Sequences too similar or too divergent
- Try filtering to more complete prophages

**Very long branch lengths**
- Some prophages highly divergent
- Check alignment quality
- Consider removing outliers

**Low bootstrap support throughout**
- Insufficient data for resolution
- Conflicting phylogenetic signal
- Try different substitution models

## Publication Checklist

For publication-quality tree:

- [ ] Use consensus tree with bootstrap support
- [ ] Show scale bar (substitutions per site)
- [ ] Label major clades
- [ ] Color by meaningful metadata (year/host)
- [ ] Include bootstrap values >70%
- [ ] Export as vector (SVG/PDF) not raster
- [ ] Caption describes: method, model, bootstrap replicates
- [ ] Report alignment length and number of sequences

## Citation

If using this tree in publications, cite:

- **IQ-TREE**: Minh et al. (2020) Mol Biol Evol 37:1530-1534
- **MAFFT**: Katoh & Standley (2013) Mol Biol Evol 30:772-780
- **Your pipeline**: COMPASS v1.2 (github.com/your-repo)

## Next Steps

1. Visualize tree with iTOL or FigTree
2. Identify major prophage clades
3. Cross-reference with AMR gene analysis
4. Check for temporal/spatial patterns
5. Prepare publication figures

---

**Generated**: $(date)
**Dataset**: Kansas NARMS 2021-2025
**Sequences**: $NUM_SEQS prophages
**Analysis**: MAFFT + IQ-TREE (1000 bootstraps)
EOF

echo "✅ Visualization guide created: $GUIDE_FILE"

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo "=========================================="
echo "🎉 PHYLOGENETIC ANALYSIS COMPLETE!"
echo "=========================================="
echo ""
echo "End time: $(date)"
echo ""
echo "📁 Output Directory: $OUTPUT_DIR"
echo ""
echo "📊 Output Files:"
echo "   Tree Files:"
echo "     - prophage_tree.treefile (best ML tree)"
echo "     - prophage_tree.contree (consensus tree with bootstrap)"
echo "     - prophage_tree.iqtree (full report)"
echo ""
echo "   Sequence Files:"
echo "     - prophages_all.fasta (original sequences)"
echo "     - prophages_aligned.fasta (aligned sequences)"
echo ""
echo "   Metadata:"
echo "     - prophage_metadata.tsv (sample information)"
echo ""
echo "   Documentation:"
echo "     - VISUALIZATION_GUIDE.md (how to visualize)"
echo ""
echo "🌳 Next Steps:"
echo ""
echo "1. Download tree file:"
echo "   scp tylerdoe@beocat.ksu.edu:$OUTPUT_DIR/prophage_tree.treefile ."
echo ""
echo "2. Visualize with iTOL:"
echo "   - Go to https://itol.embl.de/"
echo "   - Upload prophage_tree.treefile"
echo "   - Color by year/organism"
echo ""
echo "3. Or use FigTree:"
echo "   figtree prophage_tree.treefile"
echo ""
echo "4. Read visualization guide:"
echo "   cat $OUTPUT_DIR/VISUALIZATION_GUIDE.md"
echo ""
echo "=========================================="

exit 0
