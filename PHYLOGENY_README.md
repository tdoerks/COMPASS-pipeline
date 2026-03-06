# Kansas Prophage Phylogenetic Analysis

This directory contains scripts for building phylogenetic trees from prophage sequences detected in the Kansas 2021-2025 NARMS dataset.

## Overview

The phylogeny workflow consists of three main steps:

1. **Preparation**: Extract complete, high-quality prophages from VIBRANT results
2. **Alignment**: Align prophage sequences using MAFFT
3. **Tree Building**: Construct maximum likelihood tree using IQ-TREE

## Quick Start

### Option 1: Small Dataset (<500 prophages)

```bash
# On Beocat
cd /bulk/tylerdoe/archives/compass_kansas_results

# Create output directory
mkdir -p phylogeny
cd phylogeny

# 1. Extract prophages
python3 ~/COMPASS-pipeline/prepare_kansas_phylogeny.py \
    --results-dir /bulk/tylerdoe/archives/compass_kansas_results \
    --output-dir .

# 2. Align sequences (interactive - only if <500 sequences)
bash ~/COMPASS-pipeline/run_align_kansas.sh

# 3. Build tree
sbatch ~/COMPASS-pipeline/build_phylogeny_kansas.slurm
```

### Option 2: Large Dataset (>500 prophages) - Use Subsampling

```bash
# After step 1 above, subsample to manageable size
python3 ~/COMPASS-pipeline/bin/subsample_prophages_for_phylogeny.py \
    --strategy representative \
    --n 200 \
    --input-fasta kansas_complete_prophages.fasta \
    --input-metadata kansas_prophage_metadata.tsv \
    --output-fasta kansas_subsample.fasta \
    --output-metadata kansas_subsample_metadata.tsv

# Align subsampled sequences
mafft --auto --thread 16 kansas_subsample.fasta > kansas_subsample_aligned.fasta

# Update build_phylogeny_kansas.slurm to use kansas_subsample_aligned.fasta
# Then submit:
sbatch ~/COMPASS-pipeline/build_phylogeny_kansas.slurm
```

## Detailed Workflow

### Step 1: Extract Complete Prophages

The preparation script (`prepare_kansas_phylogeny.py`) does the following:

- Searches all VIBRANT results for high-quality prophages
- Filters for complete/high-quality prophages ≥15kb
- Extracts sequences from `phages_combined.fna` files
- Links to sample metadata (organism, year, sample name)
- Generates summary statistics

**Output files:**
- `kansas_complete_prophages.fasta` - All complete prophage sequences
- `kansas_prophage_metadata.tsv` - Metadata for tree annotation
- `phylogeny_stats.txt` - Summary statistics

**Quality criteria:**
- VIBRANT quality: "complete" or "high quality"
- Minimum length: 15,000 bp (default, adjustable with `--min-length`)

### Step 2: Multiple Sequence Alignment

Alignment is performed with **MAFFT**, a fast and accurate aligner suitable for viral sequences.

**Key MAFFT parameters:**
- `--auto`: Automatically selects best algorithm based on dataset size
- `--thread 16`: Uses 16 CPU cores for parallelization
- `--adjustdirection`: Allows reverse complement (important for phages!)

**Runtime estimates:**
- 50 sequences: ~5 minutes
- 200 sequences: ~30 minutes
- 500 sequences: ~2-4 hours
- 1000+ sequences: ~12+ hours (consider subsampling!)

**For large datasets:** Run alignment as SLURM job or subsample first

### Step 3: Phylogenetic Tree Construction

Tree building uses **IQ-TREE 2**, a fast and accurate maximum likelihood method.

**IQ-TREE parameters:**
- `-m MFP`: ModelFinder Plus (auto-selects best substitution model)
- `-bb 1000`: 1000 ultrafast bootstrap replicates (for support values)
- `-nt AUTO`: Auto-detects available threads

**Output files:**
- `kansas_tree.treefile` - **Final tree in Newick format (USE THIS)**
- `kansas_tree.iqtree` - Full report with model selection details
- `kansas_tree.log` - Detailed execution log
- `kansas_tree.bionj` - Initial neighbor-joining tree

**Runtime:** 1-4 hours for 200-500 sequences (depends on sequence length and diversity)

## Subsampling Strategies

For large datasets (>500 prophages), subsampling is recommended:

### 1. Representative Sampling (Recommended)
Balanced across years and organisms:
```bash
python3 bin/subsample_prophages_for_phylogeny.py \
    --strategy representative \
    --n 200
```

### 2. Top N Most Complete
Selects longest (most complete) prophages:
```bash
python3 bin/subsample_prophages_for_phylogeny.py \
    --strategy top \
    --n 200
```

### 3. Balanced by Year
Equal representation from each year:
```bash
python3 bin/subsample_prophages_for_phylogeny.py \
    --strategy by_year \
    --n-per-year 40
```

### 4. Random Sampling
Random selection (less recommended):
```bash
python3 bin/subsample_prophages_for_phylogeny.py \
    --strategy random \
    --n 200
```

## Tree Visualization

### Option 1: iTOL (Online, Interactive) - RECOMMENDED

1. Go to https://itol.embl.de/
2. Click "Upload" and select `kansas_tree.treefile`
3. Click "Datasets" → "Upload annotation files"
4. Upload `kansas_prophage_metadata.tsv`
5. Configure visualization:
   - Color branches by `year` column
   - Add labels from `organism` column
   - Show bootstrap support values
   - Export as SVG for publication

**Download files to your computer first:**
```bash
# On your local machine
scp tylerdoe@beocat.cis.ksu.edu:/bulk/tylerdoe/archives/compass_kansas_results/phylogeny/kansas_tree.treefile .
scp tylerdoe@beocat.cis.ksu.edu:/bulk/tylerdoe/archives/compass_kansas_results/phylogeny/kansas_prophage_metadata.tsv .
```

### Option 2: FigTree (Desktop Application)

```bash
# On Beocat (if X11 forwarding is set up)
module load FigTree
figtree kansas_tree.treefile
```

### Option 3: ggtree (R - Publication Quality)

```R
library(ggtree)
library(ggplot2)
library(dplyr)

# Load tree and metadata
tree <- read.tree("kansas_tree.treefile")
metadata <- read.table("kansas_prophage_metadata.tsv",
                      header=TRUE, sep="\t",
                      stringsAsFactors=FALSE)

# Join metadata to tree
p <- ggtree(tree) %<+% metadata +
  geom_tree() +
  geom_tippoint(aes(color=as.factor(year)), size=2) +
  geom_tiplab(aes(label=organism), size=2, offset=0.01) +
  theme_tree2() +
  scale_color_viridis_d(name="Year") +
  labs(title="Kansas Prophage Phylogeny (2021-2025)")

# Save high-resolution figure
ggsave("kansas_prophage_tree.png", p, width=12, height=16, dpi=300)
ggsave("kansas_prophage_tree.pdf", p, width=12, height=16)
```

## Interpreting Results

### What to Look For

1. **Temporal Clustering**: Do prophages from the same year cluster together?
   - Suggests year-specific phage populations
   - May indicate temporal turnover

2. **Host Specificity**: Do prophages cluster by bacterial host organism?
   - Salmonella vs. E. coli vs. Campylobacter
   - Suggests host-specific phage adaptation

3. **Geographic Patterns**: Do Kansas samples cluster separately?
   - Compare to national NARMS data (if available)
   - Suggests regional phage populations

4. **Prophage Movement**: Do identical/nearly identical prophages appear across:
   - Different years → longitudinal persistence
   - Different organisms → horizontal transfer
   - Different samples → transmission/spread

### Bootstrap Support Values

- **≥70%**: Strong support, reliable clade
- **50-69%**: Moderate support, interpret cautiously
- **<50%**: Weak support, topology uncertain

### Important Caveats

⚠️ **These are prophage regions, not complete genomes**
- Prophages may be fragmented or partial
- VIBRANT identifies high-quality regions, but they may not be full phage genomes
- Phylogenetic relationships should be interpreted with this in mind

⚠️ **Recombination can complicate phylogeny**
- Phages frequently recombine
- Tree assumes vertical descent (no recombination)
- Consider recombination analysis (PHI test, RDP4) for robust interpretation

## Troubleshooting

### Problem: "No VIBRANT results found"

**Solution:** Check that VIBRANT analysis completed successfully
```bash
find /bulk/tylerdoe/archives/compass_kansas_results -name "VIBRANT_genome_quality_*.tsv" | head
```

### Problem: "0 complete prophages found"

**Possible causes:**
- VIBRANT didn't find high-quality prophages (rare)
- Incorrect quality threshold

**Solution:** Lower minimum length threshold
```bash
python3 prepare_kansas_phylogeny.py --min-length 10000
```

### Problem: Alignment is taking too long

**Solution:** Subsample to ≤200 sequences, or run as SLURM job:
```bash
#SBATCH --time=12:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=16

module load MAFFT
mafft --auto --thread 16 kansas_complete_prophages.fasta > kansas_aligned.fasta
```

### Problem: IQ-TREE fails with "not enough sequences"

**Cause:** Need at least 4 sequences for phylogenetic analysis

**Solution:** Check prophage extraction - may need to adjust quality filters

### Problem: Tree looks like a "star" (no structure)

**Possible causes:**
- Sequences are too divergent (no phylogenetic signal)
- Alignment quality is poor
- Dataset includes very different phage types

**Solutions:**
1. Check alignment visually (use Jalview or AliView)
2. Filter for specific phage types (check VIBRANT annotations)
3. Try protein alignment instead of nucleotide
4. Use only certain prophage genes (e.g., major capsid protein)

## Advanced Options

### Protein-Based Phylogeny

For very divergent phages, protein phylogeny may work better:

```bash
# Extract protein sequences from VIBRANT
# (Custom script needed - prophage CDS sequences)

# Align with MAFFT
mafft --auto proteins.fasta > proteins_aligned.fasta

# Build tree
iqtree2 -s proteins_aligned.fasta -m MFP -bb 1000 -nt AUTO
```

### Gene-Specific Trees

Build trees for specific phage genes (e.g., terminase, major capsid):

```bash
# Extract specific gene from VIBRANT annotation files
# Align and build tree as above
```

### Dating the Tree (Time-Scaled Phylogeny)

If you want to estimate divergence times:

```bash
# Use BEAST2 or TreeTime
# Requires sampling dates (already in metadata as 'year')
```

## File Structure

After running the full workflow, your directory should contain:

```
phylogeny/
├── kansas_complete_prophages.fasta      # All extracted prophages
├── kansas_prophage_metadata.tsv         # Sample metadata
├── phylogeny_stats.txt                  # Summary statistics
├── kansas_aligned.fasta                 # Aligned sequences
├── kansas_tree.treefile                 # Final phylogenetic tree (Newick)
├── kansas_tree.iqtree                   # IQ-TREE detailed report
├── kansas_tree.log                      # IQ-TREE log
└── kansas_tree.bionj                    # Initial NJ tree
```

## References

**Tools:**
- MAFFT: Katoh K, Standley DM. (2013) MAFFT multiple sequence alignment software version 7. _Mol Biol Evol_ 30(4):772-780.
- IQ-TREE: Minh BQ, et al. (2020) IQ-TREE 2: New models and efficient methods for phylogenetic inference. _Mol Biol Evol_ 37(5):1530-1534.
- VIBRANT: Kieft K, Zhou Z, Anantharaman K. (2020) VIBRANT: automated recovery, annotation and curation of microbial viruses. _Microbiome_ 8:90.

**Visualization:**
- iTOL: Letunic I, Bork P. (2021) Interactive Tree Of Life (iTOL) v5. _Nucleic Acids Res_ 49(W1):W293-W296.
- ggtree: Yu G, et al. (2017) ggtree: an R package for visualization of tree and annotation data. _Methods Ecol Evol_ 8(1):28-36.

## Questions?

For issues specific to:
- **COMPASS pipeline**: See main CLAUDE.md
- **VIBRANT output**: Check VIBRANT documentation
- **IQ-TREE errors**: See http://www.iqtree.org/doc/
- **Tree visualization**: iTOL tutorials at https://itol.embl.de/help.cgi
