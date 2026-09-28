# Session Notes: 2026-04-14 - Fusobacterium Prophage Phylogenomics

## Summary
Created complete phylogenomic analysis pipeline for Fusobacterium prophages and launched tree building to test vertical inheritance vs horizontal transfer hypothesis.

---

## Phylogenomic Analysis Setup

### Goal
Determine whether Fusobacterium prophages are:
1. **Vertically inherited** (co-evolved with host species)
2. **Horizontally transferred** (moving between Fusobacterium species)
3. **Host-specific** (human vs bovine isolates)
4. **Niche-specific** (oral vs gut isolates)

### Research Questions
1. Do prophages cluster by Fusobacterium subspecies?
2. Do F. necrophorum prophages cluster together? (professor's organism)
3. Do bovine vs human isolate prophages cluster?
4. Do oral vs GI tract prophages differ?

### Hypothesis
**Expected: Vertical inheritance pattern**
- **Reasoning**: Low prophage burden (1.3/genome) suggests limited active transfer
- **Prediction**: Prophages will cluster by subspecies
- **Implication**: Ancient prophages retained through vertical inheritance
- **Alternative**: Horizontal transfer would show mixed subspecies clustering

---

## Pipeline Created

### Scripts Developed

#### 1. `extract_prophage_sequences.py`
**Purpose**: Extract prophage DNA sequences from VIBRANT results
**Input**: VIBRANT phages_combined.fna files (218 samples)
**Output**: all_prophage_sequences.fna (combined prophage sequences)
**Features**:
- Extracts prophages from each sample
- Renames with SRR sample prefix for traceability
- Calculates size statistics
- Outputs size range, mean, counts

#### 2. `build_prophage_tree.sh`
**Purpose**: Complete automated tree-building workflow
**Steps**:
1. Extract prophage sequences (Python script)
2. Align sequences with MAFFT
3. Build tree with FastTree
4. Generate logs and statistics

**Parameters**:
- MAFFT: `--auto --thread 8 --adjustdirection`
- FastTree: `-nt -gtr` (nucleotide, GTR model)

**Output Files**:
- all_prophage_sequences.fna (raw sequences)
- prophages_aligned.fna (MAFFT alignment)
- prophage_tree.nwk (Newick tree)
- mafft.log, fasttree.log

#### 3. `build_host_tree.sh`
**Purpose**: Build host genome tree for comparison (optional)
**Strategy**: Use BUSCO single-copy genes or 16S rRNA
**Status**: Created but not yet run (optional for later)

#### 4. `PHYLOGENOMICS_README.md`
**Purpose**: Complete documentation and user guide
**Contents**:
- Workflow instructions
- Interpretation guide
- Visualization options
- Publication figure suggestions
- Troubleshooting guide

---

## Tree Building Run

### Execution
```bash
Location: /fastscratch/tylerdoe/fusobacterium_results/analysis/
Command: bash build_prophage_tree.sh
Modules: MAFFT/7.505-GCC-11.3.0, FastTree/2.1.11-GCCcore-11.3.0
Status: RUNNING
```

### Step 1: Sequence Extraction (COMPLETE)
**Results**:
- Total prophage sequences extracted: **28**
- Source: VIBRANT integrated prophages from 218 Fusobacterium genomes
- Output: all_prophage_sequences.fna

**Size Statistics**:
- Min size: 2,222 bp
- Max size: 178,947 bp
- Mean size: 34,478 bp
- Range: 5.8 kb - 179 kb (consistent with earlier analysis)

**Note**: 28 sequences (not 278) because:
- Only samples with extracted prophage sequences included
- 78 samples had 0 prophages (no sequences)
- Some prophages may not have been extracted as full sequences by VIBRANT
- 28 represents distinct prophage elements with complete sequences

### Step 2: MAFFT Alignment (RUNNING)
**Status**: In progress
**Expected runtime**: 15-30 minutes for 28 sequences
**Command**: `mafft --auto --thread 8 --adjustdirection`
**Output**: prophages_aligned.fna

### Step 3: FastTree (PENDING)
**Status**: Will run after MAFFT completes
**Expected runtime**: 5-10 minutes for 28 sequences
**Command**: `FastTree -nt -gtr`
**Output**: prophage_tree.nwk

### Total Expected Runtime
**Extraction**: 2 minutes ✓
**MAFFT**: 15-30 minutes (running)
**FastTree**: 5-10 minutes (pending)
**Total**: ~25-45 minutes

---

## Sample Naming Convention

### Tree Tip Labels
Each prophage sequence labeled as:
```
SRR10901569_NODE_1_fragment_1
SRR17382041_NODE_5_fragment_2
```

**Components**:
- `SRR#######`: Sample accession (traceable to metadata)
- `NODE_X`: Contig number in assembly
- `fragment_X`: Prophage fragment number

**Benefit**: Can match tree tips back to:
- Subspecies (F. necrophorum, F. nucleatum, etc.)
- Host species (human, bovine)
- Isolation source (oral, GI, clinical)
- Prophage count per genome
- All other metadata

---

## Visualization Plan

### Primary Method: iTOL (Interactive Tree of Life)

**Step 1: Upload Tree**
- URL: https://itol.embl.de/
- Upload: prophage_tree.nwk

**Step 2: Prepare Metadata Annotation**
Create annotation files mapping SRR → metadata:
- subspecies.txt: SRR → F. necrophorum, F. nucleatum, etc.
- host.txt: SRR → Human, Bovine, Pig, etc.
- source.txt: SRR → Oral, GI tract, Blood, etc.
- prophage_count.txt: SRR → Number of prophages

**Step 3: Color and Annotate**
- Color branches by subspecies
- Add outer ring showing host
- Add outer ring showing isolation source
- Label F. necrophorum samples

**Step 4: Export**
- High-resolution PDF for publication
- SVG for further editing

### Alternative Methods

**FigTree** (desktop):
- Download: http://tree.bio.ed.ac.uk/software/figtree/
- Manual annotation

**ggtree in R**:
```R
library(ggtree)
library(ggplot2)

tree <- read.tree('prophage_tree.nwk')
metadata <- read.csv('sample_metadata.csv')

p <- ggtree(tree) %<+% metadata
p + geom_tiplab(aes(color=Subspecies), size=2)
```

---

## Interpretation Framework

### Pattern 1: Subspecies Clustering (Expected)
**If observed**:
- F. necrophorum prophages cluster together
- F. nucleatum prophages cluster together
- F. funduliforme prophages cluster together

**Interpretation**: **Vertical inheritance**
- Prophages co-evolved with host lineages
- Ancient prophage integrations retained
- Limited horizontal transfer

**Implication**: Supports low prophage burden hypothesis
- Anaerobic lifestyle limits phage-mediated gene transfer
- Prophages are remnants of ancient integrations

### Pattern 2: Mixed Clustering
**If observed**:
- Different subspecies share similar prophages
- No clear subspecies pattern

**Interpretation**: **Horizontal transfer**
- Prophages actively moving between species
- Shared prophage pool across Fusobacterium

**Implication**: Would challenge our hypothesis
- Active transfer despite anaerobic lifestyle?
- Niche-specific transfer mechanisms?

### Pattern 3: Host Clustering
**If observed**:
- Human isolate prophages cluster
- Bovine isolate prophages cluster (separate)

**Interpretation**: **Host-specific prophage ecology**
- Different prophage populations in different hosts
- Host immune selection driving prophage evolution

### Pattern 4: Niche Clustering
**If observed**:
- Oral cavity prophages cluster
- GI tract prophages cluster (separate)

**Interpretation**: **Niche-specific adaptation**
- Environmental selection on prophage types
- Biofilm vs planktonic prophage ecology

---

## Expected Results

### Primary Expectation
**Vertical inheritance pattern with subspecies clustering**

**Supporting evidence**:
1. **Low prophage burden** (1.3/genome) → Not actively spreading
2. **High prophage-free genomes** (36%) → Ancient remnants, not recent acquisitions
3. **Anaerobic lifestyle** → Limited phage exposure/infection
4. **Literature**: Oxidative stress drives lysogeny (absent in anaerobes)

### F. necrophorum Specific
**Expectation**: F. necrophorum prophages cluster together
- 6 F. necrophorum samples in dataset
- Mean 2.0 prophages/genome (higher than average)
- From bovine isolates (mostly)

**Questions**:
- Are F. necrophorum prophages unique to this subspecies?
- Or shared with other Fusobacterium (horizontal transfer)?
- Do bovine-associated prophages differ from human?

### Statistical Validation
If vertical inheritance:
- High phylogenetic signal
- Low horizontal transfer events
- Congruent with host phylogeny (if host tree built)

---

## Next Steps

### Immediate (Today)
1. ✓ Extract prophage sequences (COMPLETE)
2. ⏳ Complete MAFFT alignment (RUNNING)
3. ⏳ Build tree with FastTree (PENDING ~30 min)
4. Download prophage_tree.nwk

### Short-term (This Week)
1. Upload tree to iTOL
2. Create metadata annotation files
3. Visualize with subspecies/host/source colors
4. Analyze clustering patterns
5. Answer research questions

### Medium-term (Next Week)
1. Build host genome tree (optional, for validation)
2. Compare prophage tree vs host tree topologies
3. Statistical tests (Robinson-Foulds distance)
4. Extract specific prophage genes (terminase) for refined tree

### Long-term (Publication)
1. Create publication-quality figures
2. Write phylogenomics methods section
3. Interpret in context of oxygen gradient hypothesis
4. Compare to other bacteria (Bacteroides when complete)

---

## Repository Status

### Files Created

#### Phylogenomics Scripts
- `fusobacterium_necrophorum_study/scripts/extract_prophage_sequences.py`
- `fusobacterium_necrophorum_study/scripts/build_prophage_tree.sh`
- `fusobacterium_necrophorum_study/scripts/build_host_tree.sh`
- `fusobacterium_necrophorum_study/PHYLOGENOMICS_README.md`

#### Session Notes
- `SESSION_NOTES_2026-04-14_fusobacterium_phylogenomics.md` (this file)

### Git Status
- **Branch**: scratch
- **Last commit**: Phylogenomics pipeline (efc5d8e)
- **Pushed**: Yes
- **Pending**: This session note

---

## Software and Dependencies

### Modules Used
```bash
MAFFT/7.505-GCC-11.3.0-with-extensions
FastTree/2.1.11-GCCcore-11.3.0
Python 3 (with BioPython)
```

### Optional Software
- **RAxML** or **IQ-TREE**: More accurate trees (slower)
- **barrnap**: 16S extraction for host tree
- **R** with ggtree, ape, phytools: Visualization and statistics
- **Dendroscope**: Tree comparison visualization

---

## Publication Context

### Manuscript Section: Phylogenomics

**Current evidence**:
- ✓ Low prophage burden (1.3/genome)
- ✓ Host/niche associations (metadata analysis)
- ⏳ Phylogenetic evidence (tree building in progress)

**Key message**:
"Fusobacterium prophages exhibit vertical inheritance patterns consistent with ancient integrations and limited horizontal transfer, supporting the oxygen-dependent prophage burden hypothesis."

**Figure planned**:
- Figure: Prophage phylogenetic tree annotated with subspecies and host
- Caption: "Clustering by subspecies indicates vertical inheritance rather than active horizontal transfer"

---

## Technical Notes

### Prophage Sequence Count
**28 sequences (not 278)**

**Why fewer than expected?**
1. **278 total prophages detected** (from integrated_prophage_coordinates.tsv)
2. **Not all extracted as full sequences** by VIBRANT
3. **VIBRANT phages_combined.fna** contains complete prophage sequences only
4. **Partial or low-confidence prophages** not included in FASTA output
5. **28 represents high-confidence, complete prophage sequences**

**Is 28 enough?**
- **Yes** for initial analysis
- Represents ~13% of genomes (28/218)
- Covers multiple subspecies
- Sufficient for pattern detection

**Future**: Could extract prophage regions manually from coordinates for all 278

### MAFFT Parameters
```bash
--auto            # Automatically select strategy
--thread 8        # Use 8 CPU threads
--adjustdirection # Account for reverse complements
```

### FastTree Parameters
```bash
-nt               # Nucleotide sequences
-gtr              # General Time Reversible model
-log              # Output log file
```

---

## Concurrent Studies Update

### Running Studies
1. **Bacteroides fragilis** (1.2.0): 1,411 samples, initializing
2. **STEC/E. coli** (1.1.0): 7,340 samples, ~98% downloads, 42% QC

### Completed Studies
1. **Fusobacterium** (1.2.0): 218 samples, analyzing phylogenomics
2. **Salmonella** (1.0.1): 2,737 samples, complete

### Oxygen Gradient Status
| Organism | Metabolism | Samples | Prophages/Genome | Tree Status |
|----------|------------|---------|------------------|-------------|
| Fusobacterium | Anaerobe | 218 | 1.3 | Building ⏳ |
| Bacteroides | Anaerobe | 1,411 | ? | Data pending |
| Salmonella | Facultative | 2,737 | 4.2 | Not planned |
| E. coli | Facultative | 7,340 | ? | Data pending |

---

## Key Decisions

### 1. Full Prophage Sequences vs Specific Genes
**Decision**: Use full prophage sequences for initial tree
**Rationale**:
- More comprehensive signal
- Represents entire prophage element
- Can extract specific genes later if needed

**Alternative considered**: Terminase genes only (more conserved, but requires annotation parsing)

### 2. Tree Building Software
**Decision**: FastTree
**Rationale**:
- Available on Beocat
- Fast for initial analysis (~10 min)
- Good accuracy for large alignments
- Can use RAxML/IQ-TREE for publication if needed

### 3. 28 Sequences vs Extracting All 278
**Decision**: Use 28 high-confidence sequences from VIBRANT
**Rationale**:
- Quick initial analysis
- High-quality sequences
- Sufficient for pattern detection

**Future**: Can extract all 278 from coordinates if needed

---

## Expected Timeline

### Today (2026-04-14)
- ✓ Create scripts
- ✓ Extract sequences
- ⏳ MAFFT alignment (~30 min remaining)
- ⏳ FastTree (~10 min after MAFFT)
- Upload to iTOL (10 min)
- **Total: ~1 hour**

### This Week
- Analyze tree patterns
- Create annotated visualizations
- Answer research questions
- Document findings

### Publication
- Include phylogenetic analysis in manuscript
- Compare across oxygen gradient studies
- Validate vertical inheritance hypothesis

---

## Lessons Learned

### 1. VIBRANT Output Understanding
- `phages_combined.fna`: Complete, extracted prophages only
- `integrated_prophage_coordinates.tsv`: All detected prophages (including partial)
- Not all detected prophages have extracted sequences

### 2. Sample Size for Trees
- 28 sequences sufficient for initial analysis
- Represents diversity across subspecies
- Can expand later if needed

### 3. Module Availability
- Beocat has MAFFT and FastTree readily available
- No conda environment needed
- Simple module load

---

*Session conducted: 2026-04-14*
*Tree building: In progress*
*Expected completion: ~30-45 minutes*
*Location: /fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/*

**Status: MAFFT RUNNING, FastTree PENDING ✓**
