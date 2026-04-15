# Fusobacterium Prophage Phylogenomic Analysis

## Overview
Phylogenetic analysis of Fusobacterium prophages to determine:
- **Vertical inheritance** (prophages co-evolve with host)
- **Horizontal transfer** (prophages move between species)
- **Niche-specific** patterns (oral vs gut prophages)
- **Host-specific** patterns (human vs bovine)

## Research Questions

### Primary Questions
1. **Do prophages cluster by Fusobacterium subspecies?**
   - If YES → Vertical inheritance (ancient prophages co-evolving with hosts)
   - If NO → Horizontal transfer (prophages moving between species)

2. **Do F. necrophorum prophages cluster together?**
   - Unique to F. necrophorum (cattle pathogen)?
   - Or shared with other Fusobacterium species?

3. **Do bovine vs human isolate prophages cluster?**
   - Host-specific prophage populations?
   - Or cross-host transfer?

4. **Do oral vs GI tract prophages differ?**
   - Niche-specific prophage adaptation?

### Secondary Questions
5. Do prophage-rich genomes share similar prophage types?
6. Are large prophages (>50 kb) phylogenetically distinct from small ones?
7. Do clinical vs commensal isolates have different prophage lineages?

## Workflow

### Quick Start (Recommended)

```bash
# On Beocat
cd /fastscratch/tylerdoe/fusobacterium_results/analysis/

# Run the complete workflow
bash /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/scripts/build_prophage_tree.sh
```

This will:
1. Extract all 278 prophage sequences from VIBRANT results
2. Align with MAFFT (~15-30 minutes)
3. Build tree with FastTree (~10-20 minutes)
4. Output: `phylogenomics/prophage_tree.nwk`

### Step-by-Step

#### Step 1: Extract Prophage Sequences
```bash
cd /fastscratch/tylerdoe/fusobacterium_results/analysis/

python3 /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/scripts/extract_prophage_sequences.py
```

**Output**: `all_prophage_sequences.fna` (~278 prophage sequences)

#### Step 2: Align Sequences
```bash
# Load MAFFT
module load MAFFT  # or: conda install -c bioconda mafft

# Align prophages
mafft --auto --thread 8 --adjustdirection \
      all_prophage_sequences.fna \
      > prophages_aligned.fna
```

**Runtime**: 15-30 minutes for ~278 sequences

#### Step 3: Build Phylogenetic Tree
```bash
# Load FastTree
module load FastTree  # or: conda install -c bioconda fasttree

# Build tree
FastTree -nt -gtr \
         -log fasttree.log \
         prophages_aligned.fna \
         > prophage_tree.nwk
```

**Runtime**: 10-20 minutes

#### Step 4: Visualize Tree

**Option A: iTOL (Interactive Tree of Life) - RECOMMENDED**
1. Go to https://itol.embl.de/
2. Upload `prophage_tree.nwk`
3. Upload metadata for annotation:
   - Subspecies (F. nucleatum, F. necrophorum, etc.)
   - Host (human, bovine)
   - Isolation source (oral, GI, clinical)
4. Color branches by metadata
5. Export publication-quality figure

**Option B: FigTree (Local)**
1. Download FigTree: http://tree.bio.ed.ac.uk/software/figtree/
2. Open `prophage_tree.nwk`
3. Manually annotate with metadata

**Option C: R with ggtree**
```R
library(ggtree)
library(ggplot2)

# Load tree
tree <- read.tree('prophage_tree.nwk')

# Load metadata
metadata <- read.csv('sample_metadata.csv')

# Basic tree
ggtree(tree) + geom_tiplab(size=2)

# Tree with metadata
p <- ggtree(tree) %<+% metadata
p + geom_tiplab(aes(color=Subspecies), size=2)
```

## Interpretation Guide

### Pattern 1: Subspecies Clustering
```
If tree shows:
├─ F. nucleatum prophages clustered
├─ F. necrophorum prophages clustered
└─ F. funduliforme prophages clustered

INTERPRETATION: Vertical inheritance
  - Prophages co-evolved with host species
  - Ancient prophage integrations
  - Species-specific prophage populations
```

### Pattern 2: No Subspecies Pattern
```
If tree shows:
├─ Mixed subspecies in each clade
├─ F. necrophorum + F. nucleatum together
└─ No clear host pattern

INTERPRETATION: Horizontal transfer
  - Prophages actively transferring between species
  - Shared prophage pool
  - Recent prophage acquisitions
```

### Pattern 3: Host Clustering
```
If tree shows:
├─ Human isolate prophages clustered
└─ Bovine isolate prophages clustered

INTERPRETATION: Host-specific prophage ecology
  - Different prophage populations in different hosts
  - Host immune selection?
  - Environment drives prophage diversity
```

### Pattern 4: Niche Clustering
```
If tree shows:
├─ Oral isolate prophages clustered
└─ GI tract prophages clustered

INTERPRETATION: Niche-specific prophage adaptation
  - Oral biofilm prophages differ from gut
  - Environmental selection on prophage types
```

## Expected Results

### Hypothesis
Based on low prophage burden (1.3/genome) and high prophage-free genomes (36%), we expect:

**LIKELY**: Vertical inheritance pattern
- **Reasoning**: Low burden suggests prophages are not actively spreading
- **Expectation**: Prophages cluster by subspecies
- **Implication**: Ancient prophages retained through vertical inheritance

**LESS LIKELY**: Active horizontal transfer
- **Reasoning**: Would lead to higher prophage burden
- **Expectation**: Would see mixed subspecies clustering
- **Implication**: Anaerobic lifestyle limits phage-mediated transfer?

## Advanced Analysis (Optional)

### Compare to Host Genome Tree

To definitively prove co-evolution vs horizontal transfer:

```bash
# Build host tree (see build_host_tree.sh)
bash /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/scripts/build_host_tree.sh
```

**Compare topologies**:
- **Congruent trees** → Co-evolution (vertical inheritance)
- **Incongruent trees** → Horizontal transfer

**Tools for comparison**:
- Dendroscope (visual comparison)
- TreeCmp (statistical comparison)
- R packages: `phytools`, `ape`

### Extract Specific Prophage Genes

For more focused analysis, extract conserved prophage markers:

**Terminase (most conserved)**:
```bash
# From PHANOTATE results
# Search for terminase annotations
grep -i "terminase" phanotate/*.txt

# Extract terminase sequences
# Build gene-specific tree
```

**Integrase**:
```bash
# Shows integration sites
# Indicates host range
```

### Statistical Tests

**Robinson-Foulds Distance** (tree comparison):
```R
library(ape)
library(phangorn)

prophage_tree <- read.tree('prophage_tree.nwk')
host_tree <- read.tree('host_tree.nwk')

RF.dist(prophage_tree, host_tree)
```

**Congruence Test**:
```R
library(geiger)
congruence.test(prophage_tree, host_tree)
```

## Data Files

### Input Files (Fusobacterium Results)
```
fusobacterium_results/
├── vibrant/
│   └── SRR*_vibrant/
│       └── *_contigs.phages_combined.fna  # Prophage sequences
├── phanotate/                             # Prophage annotations
└── assemblies/                            # Host genomes
```

### Metadata Files
```
fusobacterium_necrophorum_study/data/
├── fusobacterium_metadata.tsv             # Full metadata
└── fusobacterium_metadata_prophage_merged.tsv  # Merged with prophage counts
```

### Output Files
```
fusobacterium_results/analysis/phylogenomics/
├── all_prophage_sequences.fna      # Raw prophage sequences
├── prophages_aligned.fna           # MAFFT alignment
├── prophage_tree.nwk               # Newick tree
├── sample_metadata.csv             # For iTOL annotation
├── mafft.log                       # MAFFT log
└── fasttree.log                    # FastTree log
```

## Software Requirements

### Required
- **MAFFT** (alignment): `module load MAFFT` or `conda install -c bioconda mafft`
- **FastTree** (tree): `module load FastTree` or `conda install -c bioconda fasttree`
- **Python 3** with BioPython: `pip install biopython`

### Optional
- **RAxML** or **IQ-TREE** (more accurate trees, slower)
- **barrnap** (16S extraction for host tree)
- **R** with ggtree, ape, phytools (visualization, statistics)

## Timeline

### Quick Analysis (Same Day)
- Extract sequences: 5 minutes
- MAFFT alignment: 30 minutes
- FastTree: 20 minutes
- Upload to iTOL: 10 minutes
- **Total: ~1 hour**

### Full Analysis (1-2 Days)
- Extract sequences: 5 minutes
- MAFFT alignment: 30 minutes
- FastTree: 20 minutes
- Extract host genes: 2 hours
- Build host tree: 4 hours
- Compare trees: 1 hour
- Statistics: 2 hours
- **Total: ~10 hours (can run overnight)**

## Publication Figures

### Figure 1: Prophage Phylogenetic Tree
- **Layout**: Circular or rectangular tree
- **Branch colors**: By Fusobacterium subspecies
- **Tip labels**: Sample IDs
- **Outer rings**:
  - Host species (human/bovine)
  - Isolation source (oral/GI/clinical)
  - Prophage count per genome
  - Prophage size

### Figure 2: Tanglegram (Prophage vs Host)
- **Left**: Host genome tree
- **Right**: Prophage tree
- **Lines**: Connect matching samples
- **Congruent** = vertical inheritance
- **Incongruent** = horizontal transfer

### Figure 3: Prophage Gene Content Matrix
- **Rows**: Prophage samples
- **Columns**: Prophage genes (from PHANOTATE)
- **Heatmap**: Gene presence/absence
- **Dendrogram**: From prophage tree

## Troubleshooting

### Issue: MAFFT runs out of memory
**Solution**: Use `--retree 1` for faster, less memory-intensive alignment
```bash
mafft --retree 1 --thread 8 all_prophage_sequences.fna > prophages_aligned.fna
```

### Issue: Too many sequences for clear visualization
**Solution**: Subset to representative samples
```bash
# Keep only prophages from samples with metadata
# Or sample 50 random prophages
```

### Issue: Tree has very long branches
**Meaning**: High sequence divergence
**Interpretation**: Ancient prophage integrations or different prophage families

### Issue: No clear clustering pattern
**Meaning**: Complex prophage dynamics
**Interpretation**: Mix of vertical inheritance and horizontal transfer

## References

### Phylogenetic Methods
- MAFFT: Katoh & Standley (2013) Molecular Biology and Evolution
- FastTree: Price et al. (2010) PLoS ONE
- ggtree: Yu et al. (2017) Methods in Ecology and Evolution

### Prophage Biology
- Prophage diversity: Bobay et al. (2014) Nature Communications
- Horizontal transfer: Touchon et al. (2016) ISME Journal
- Fusobacterium prophages: [Literature search needed]

---

*Part of Fusobacterium Prophage Dynamics Study*
*Oxygen Gradient Comparative Genomics Project*
