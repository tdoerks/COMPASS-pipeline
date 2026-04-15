# Fusobacterium Prophage Tree Visualization Guide

## ✅ Tree Building Complete!

**Status**: Both MAFFT alignment and FastTree building finished successfully
- **MAFFT**: Aligned 28 prophage sequences (FFT-NS-2 strategy)
- **FastTree**: Completed in 197 seconds using GTR model
- **Tree file**: `prophage_tree.nwk` (2.2K) ready at `/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/`

---

## Step 1: Download Tree File from Beocat

### Option A: Using scp (Recommended)

```bash
# From your local machine
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/prophage_tree.nwk .
```

### Option B: Using rsync

```bash
# Download tree and all related files
rsync -avz tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/ ./prophage_tree_results/
```

This will download:
- `prophage_tree.nwk` (the tree!)
- `all_prophage_sequences.fna` (raw sequences)
- `prophages_aligned.fna` (alignment)
- `mafft.log` and `fasttree.log` (logs)

---

## Step 2: Create iTOL Annotation Files (Optional but Recommended)

iTOL annotations will color the tree by subspecies, host, and isolation source.

### On Beocat:

```bash
ssh tylerdoe@beocat.cis.ksu.edu

cd /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate

# Run annotation script
python3 fusobacterium_necrophorum_study/scripts/create_itol_annotations.py
```

This creates:
- `itol_subspecies.txt` - Color by F. nucleatum, F. necrophorum, etc.
- `itol_host.txt` - Color by Human, Bovine, Pig
- `itol_source.txt` - Color by Oral, GI, Blood

### Download annotation files:

```bash
# From your local machine
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/itol_*.txt .
```

---

## Step 3: Visualize in iTOL (Interactive Tree of Life)

### Upload Tree

1. Go to **https://itol.embl.de/**
2. Click **"Upload"** button
3. Select `prophage_tree.nwk`
4. Click **"Upload"** and wait for tree to load

### Add Annotations (if created)

1. In iTOL, drag and drop annotation files:
   - `itol_subspecies.txt`
   - `itol_host.txt`
   - `itol_source.txt`

2. Or click **"Datasets"** tab → **"Upload annotation files"**

### Customize Display

**Basic settings**:
- **Display mode**: Choose Circular or Normal
- **Branch length**: Toggle to see evolutionary distances
- **Bootstrap values**: Toggle if you want support values

**Colors**:
- Click **"Advanced"** tab
- Adjust color schemes for each annotation layer

**Labels**:
- Click **"Labels"** to adjust tip label size
- Can show/hide sample IDs (SRR accessions)

### Export High-Resolution Figure

1. Click **"Export"** tab
2. Select **"Scalable Vector Graphics (SVG)"** or **"Portable Document Format (PDF)"**
3. Adjust dimensions (e.g., 3000x3000 pixels)
4. Click **"Export"** to download

---

## Step 4: Interpret the Tree

### Research Questions

1. **Do prophages cluster by Fusobacterium subspecies?**
   - Look for distinct clades colored by subspecies
   - If YES → Vertical inheritance (co-evolution with host)
   - If NO → Horizontal transfer (prophages moving between species)

2. **Do F. necrophorum prophages cluster together?**
   - Look for blue clade (if using subspecies annotation)
   - Indicates species-specific prophages

3. **Do bovine vs human isolate prophages cluster?**
   - Look for host color pattern
   - Tests host-specific prophage ecology

4. **Do oral vs GI tract prophages differ?**
   - Look for source color pattern
   - Tests niche-specific adaptation

### Expected Pattern (Hypothesis)

**LIKELY**: Vertical inheritance
- Prophages cluster by subspecies
- F. necrophorum prophages form distinct clade
- Reasoning: Low prophage burden (1.3/genome) suggests ancient integrations, not active transfer

**Alternative**: Horizontal transfer
- Prophages mixed across subspecies
- Shared prophage pool
- Would challenge our hypothesis

---

## Alternative Visualization Methods

### Option 1: FigTree (Desktop Application)

**Download**: http://tree.bio.ed.ac.uk/software/figtree/

**Usage**:
1. Open FigTree
2. File → Open → Select `prophage_tree.nwk`
3. Manually color branches
4. Export as PNG or PDF

**Pros**: Easy to use, no internet required
**Cons**: Manual annotation, less customizable than iTOL

### Option 2: ggtree in R

```R
# Install packages
install.packages("ape")
install.packages("ggtree")

# Load libraries
library(ggtree)
library(ggplot2)
library(ape)

# Load tree
tree <- read.tree("prophage_tree.nwk")

# Basic plot
ggtree(tree) + geom_tiplab(size=2)

# With metadata (if you have metadata file)
metadata <- read.csv("fusobacterium_metadata.csv")
p <- ggtree(tree) %<+% metadata
p + geom_tiplab(aes(color=Subspecies), size=2) +
    theme(legend.position="right")

# Save
ggsave("prophage_tree.pdf", width=10, height=8)
```

**Pros**: Publication-quality, highly customizable, scriptable
**Cons**: Requires R knowledge

### Option 3: Python with ete3

```python
from ete3 import Tree, TreeStyle, NodeStyle

# Load tree
t = Tree("prophage_tree.nwk")

# Basic rendering
ts = TreeStyle()
ts.show_leaf_name = True
t.render("prophage_tree.png", tree_style=ts)
```

---

## Tree File Details

### File Information
- **Location**: `/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/prophage_tree.nwk`
- **Format**: Newick format (standard phylogenetic tree format)
- **Size**: 2.2K
- **Sequences**: 28 prophage sequences from 218 Fusobacterium genomes

### Tip Labels

Each prophage labeled as:
```
SRR10901569_NODE_9_length_118569_cov_128.637039_fragment_3
```

**Components**:
- `SRR#######`: Sample accession (traceable to metadata)
- `NODE_X`: Contig number in assembly
- `length_X`: Contig length
- `cov_X`: Sequencing coverage
- `fragment_X`: Prophage fragment number

**Benefit**: Can match tree tips back to:
- Subspecies (F. necrophorum, F. nucleatum, etc.)
- Host species (human, bovine)
- Isolation source (oral, GI, clinical)
- All other metadata

### Model Used

**FastTree Settings**:
- **Model**: GTR (General Time Reversible) - standard nucleotide substitution model
- **Rate heterogeneity**: 20 categories (accounts for different mutation rates across sites)
- **Total time**: 197.84 seconds
- **Log-likelihood**: -1004730.9976

---

## Analysis Checklist

After visualizing the tree, answer these questions:

- [ ] Tree uploaded to iTOL successfully
- [ ] Annotations added (subspecies, host, source)
- [ ] Tree displays correctly
- [ ] Tip labels readable
- [ ] High-resolution figure exported

**Interpretation**:
- [ ] Identified major clades
- [ ] Checked for subspecies clustering
- [ ] Examined F. necrophorum prophages
- [ ] Looked for host/niche patterns
- [ ] Documented findings

**Next steps**:
- [ ] Compare to host genome tree (optional)
- [ ] Extract specific prophage genes for refined tree (optional)
- [ ] Statistical tests for co-evolution (optional)
- [ ] Include in manuscript

---

## Troubleshooting

### Tree won't upload to iTOL
**Solution**: Check file format is plain text Newick (.nwk or .tree)

### Annotations don't match tree tips
**Solution**: Ensure sample IDs (SRR accessions) match between tree and annotation files

### Labels overlap in iTOL
**Solution**:
- Switch to circular display
- Reduce label font size
- Use "Prune tree" to show subset

### Branch lengths look weird
**Solution**: This is normal for highly divergent prophages. Toggle "Ignore branch lengths" to see topology only.

---

## Files Created

### Tree Files
- `prophage_tree.nwk` - Main tree file ✓
- `prophages_aligned.fna` - MAFFT alignment (5.3M)
- `all_prophage_sequences.fna` - Raw sequences (961K)

### Log Files
- `mafft.log` - MAFFT alignment log (20K)
- `fasttree.log` - FastTree building log (503K)

### Annotation Files (optional)
- `itol_subspecies.txt` - Subspecies color annotation
- `itol_host.txt` - Host species annotation
- `itol_source.txt` - Isolation source annotation

---

## Publication-Quality Figure Checklist

For manuscript submission:

- [ ] Tree in SVG or PDF format (vector graphics)
- [ ] Resolution ≥300 DPI (if rasterized)
- [ ] Dimensions appropriate for journal (usually 3-7 inches wide)
- [ ] Color scheme accessible (colorblind-friendly if possible)
- [ ] Legend clearly explains colors/symbols
- [ ] Scale bar visible (if showing branch lengths)
- [ ] Labels readable at publication size

**Recommended export settings** (iTOL):
- Format: SVG (scalable) or PDF
- Width: 3000-5000 pixels
- Include: Legend, scale bar, dataset labels
- Font size: 12-14 pt minimum

---

## Contact & Resources

### iTOL Help
- Website: https://itol.embl.de/
- Help: https://itol.embl.de/help.cgi
- Video tutorials: https://www.youtube.com/user/itolteam

### Tree Formats
- Newick format: http://evolution.genetics.washington.edu/phylip/newicktree.html
- Nexus format: http://wiki.christophchamp.com/index.php/NEXUS_file_format

### Phylogenetics Background
- FastTree manual: http://www.microbesonline.org/fasttree/
- MAFFT: https://mafft.cbrc.jp/alignment/software/

---

*Fusobacterium Prophage Phylogenomic Analysis*
*Tree building completed: 2026-04-15*
*Ready for visualization and interpretation*
