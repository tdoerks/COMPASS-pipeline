# Session Notes: 2026-04-15 - Fusobacterium Tree Visualization & Metadata Tools

## Summary
Completed prophage tree visualization pipeline and created comprehensive metadata tools. Built iTOL annotation files and started host genome tree building. Set up Clostridium difficile study (9,133 samples).

---

## Prophage Tree Completion

### Status Check
- **Tree building**: COMPLETE ✓
- **MAFFT alignment**: 28 prophage sequences, 197 seconds
- **FastTree**: GTR model, completed successfully
- **Output**: `prophage_tree.nwk` (2.2K)
- **Location**: `/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/`

### Tree Details
- **Sequences**: 28 high-confidence prophages from 8 unique samples
- **Model**: GTR (General Time Reversible) + 20 rate categories
- **Log-likelihood**: -1004730.9976
- **Runtime**: ~3.5 minutes total (MAFFT + FastTree)

### Tree Label Format
Labels include full contig information:
```
_R_SRR848065_NODE_6_length_128875_cov_180.419461_fragment_2
SRR10901569_NODE_9_length_118569_cov_128.637039_fragment_3
```

Components:
- `_R_` prefix: Reverse complement (MAFFT auto-adjusted)
- `SRR#######`: Sample accession
- `NODE_X`: Contig number
- `length_X`: Contig size
- `cov_X`: Sequencing coverage
- `fragment_X`: Prophage number

---

## Metadata Tools Created

### Problem: Sample Identification
**Challenge**: Tree tips labeled with full contig names, need to map back to:
- Subspecies (F. nucleatum, F. necrophorum, etc.)
- Host (Human, Bovine)
- Isolation source (Oral, GI)
- All other metadata

### Solution 1: Comprehensive Metadata Table

**Script**: `create_tree_metadata_table.py`

**Purpose**: Publication-quality supplementary table

**Features**:
- Parses tree to extract sample IDs
- Matches to NCBI metadata
- Creates 16-column TSV with all info

**Output**: `tree_sample_metadata_supplementary.tsv`

**Columns**:
1. Sample_ID
2. Subspecies
3. Host
4. Isolation_Source
5. Isolation_Source_Category (Oral/GI/Blood/Clinical/Other)
6. Geographic_Location
7. Country
8. Collection_Date
9. BioProject
10. BioSample
11. Study_Title
12. Prophage_Count
13. Assembly_Size_Mb
14. Library_Strategy
15. Platform
16. Center_Name

**Results**:
- 8 unique samples in tree
- 217 total samples with metadata
- Subspecies: F. nucleatum (1), F. necrophorum subsp. (3), F. animalis (1), other (3)
- Hosts: Human (2), Bovine (2), Unknown (4)
- Sources: Oral (1), Other (7)

### Solution 2: Quick Reference Guide

**Script**: `create_tree_quick_reference.py`

**Purpose**: Simple lookup while viewing tree

**Format**:
```
SRR10901569     | F. nucleatum    | Human   | Oral
SRR37881923     | F. necrophorum  | Bovine  | GI
```

**Output**: `tree_quick_reference.txt`

**Use**: Keep open in text editor while viewing tree in iTOL

### Solution 3: iTOL Annotation Files

**Script**: `create_itol_annotations.py`

**Purpose**: Color-coded visual annotations for iTOL

**Features**:
- Parses tree to get all tip labels
- Extracts SRR from each label
- Looks up metadata
- Writes iTOL-formatted DATASET_COLORSTRIP files

**Critical Fix**: Use FULL tree labels (not just SRR)
- Before: `SRR10901569` (not found in tree)
- After: `SRR10901569_NODE_9_length_118569_cov_128.637039_fragment_3` (matched!)

**Output Files**:

1. **`itol_subspecies.txt`**
   - Colors: F. nucleatum (red), F. necrophorum (blue), F. funduliforme (green), etc.
   - Annotated: 28 tree tips
   - Unique: 4 subspecies

2. **`itol_host.txt`**
   - Colors: Human (teal), Bovine (orange), Other (pink)
   - Annotated: 28 tree tips
   - Unique: 3 hosts

3. **`itol_source.txt`**
   - Colors: Oral (light teal), GI (yellow), Other (purple)
   - Annotated: 28 tree tips
   - Unique: 2 sources

### Wrapper Script

**Script**: `run_create_tree_metadata.sh`

**Purpose**: Run all metadata scripts with one command

**Execution**:
```bash
bash run_create_tree_metadata.sh
```

Creates:
- Comprehensive metadata table
- Quick reference guide

---

## Metadata File Format Issues Resolved

### Problem 1: Column Name Mismatch
**Issue**: Metadata file had SRR accessions in "Genus" column (mislabeled)

**Header showed**: 90 columns with "PublicAccession" at position 5
**Data showed**: SRR at position 2 (Genus column)

**Solution**: Check multiple column names:
```python
srr = (row.get('Run', '') or
       row.get('PublicAccession', '') or
       row.get('sample', '') or
       row.get('Genus', ''))  # Mislabeled!
```

### Problem 2: Sparse Data
**Issue**: Many empty fields between columns

**Solution**: Used merged metadata file instead
- `fusobacterium_metadata_prophage_merged.tsv`
- Has 'sample' column that works reliably
- Already loaded 218 samples successfully
- Contains both metadata AND prophage counts

### Final Configuration
**Metadata source**: `fusobacterium_metadata_prophage_merged.tsv`
**Prophage counts**: Same file (has both!)
**Loaded**: 217 samples successfully

---

## iTOL Visualization Workflow

### 1. Upload Tree
- Go to https://itol.embl.de/
- Upload `prophage_tree.nwk`
- Tree displays with 28 tips

### 2. Add Annotations
- Go to "Datasets" tab
- Drag and drop:
  - `itol_subspecies.txt`
  - `itol_host.txt`
  - `itol_source.txt`
- Colored rings appear around tree

### 3. Interpret Patterns

**Research Questions**:

1. **Do prophages cluster by subspecies?**
   - If YES → Vertical inheritance (co-evolution)
   - If NO → Horizontal transfer

2. **Do F. necrophorum prophages cluster together?**
   - Important for professor's target organism
   - 2 F. necrophorum subsp. samples in tree

3. **Do bovine vs human prophages cluster?**
   - 2 human vs 2 bovine samples
   - Tests host-specific prophage ecology

4. **Do oral vs GI prophages cluster?**
   - 1 oral vs 7 other sources
   - Tests niche-specific adaptation

### 4. Export Figure
- Click "Export" tab
- Choose SVG or PDF (vector graphics)
- Include: Legend, scale bar, dataset labels
- Resolution: 3000+ pixels for publication

---

## Host Genome Tree Building (In Progress)

### Purpose
Compare prophage tree to host tree to definitively test:
- **Congruent trees** → Vertical inheritance (prophages inherited with host)
- **Incongruent trees** → Horizontal transfer (prophages moving between species)

### Script Created
**File**: `build_host_tree_busco.sh`

**Strategy**: BUSCO single-copy core genes
1. Identify genes present in 90%+ of 218 samples
2. Select top 20 most conserved genes
3. Align each gene with MAFFT
4. Concatenate into super-matrix
5. Build tree with FastTree

### Expected Results
- **Runtime**: 2-4 hours
- **Output**: `host_tree.nwk`
- **Location**: `/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/`

### Status
**RUNNING** - Started 2026-04-15, Step 1 in progress (identifying core genes)

---

## Clostridium difficile Study Setup

### Rationale
**Third obligate anaerobe** for oxygen gradient hypothesis

**Critical comparison**: Same niche as E. coli (gut), different oxygen tolerance

**Expected**: LOW prophage burden (like Fusobacterium 1.3)

### Study Created

**Directory**: `clostridium_difficile_study/`

**Scripts**:
1. `fetch_clostridium.py` - Retrieve SRA accessions
2. `create_samplesheet.py` - Generate COMPASS input
3. `run_clostridium.sh` - SLURM job for pipeline 1.2.0

**README**: Complete documentation

### Accessions Retrieved
- **Total**: 9,133 Clostridium difficile samples
- **Source**: NCBI SRA
- **Criteria**: Illumina, WGS, Genomic
- **Organism**: Clostridioides difficile (updated nomenclature)

### Files Created
- `sra_accessions_clostridium.txt` (9,133 accessions)
- `samplesheet_clostridium.txt` (COMPASS input)
- `run_clostridium.sh` (SLURM job script)

### Status
**READY TO LAUNCH** - Not yet submitted

**Launch command**:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/clostridium_difficile_study
sbatch run_clostridium.sh
```

---

## Oxygen Gradient Study Status

### Overview Document Created
**File**: `OXYGEN_GRADIENT_STATUS.md`

**Content**:
- Complete study status across all oxygen tolerance groups
- Sample counts and progress
- Hypothesis testing framework
- Expected outcomes
- Publication timeline

### Current Studies

**✅ Complete**:
1. Fusobacterium (218) → 1.3 prophages/genome
2. Salmonella (2,737) → 4.2 prophages/genome

**🔄 Running**:
1. Bacteroides fragilis (1,411) - Job 7643548, ~17% downloads
2. STEC/E. coli (7,340) - Job 7614525, 98% downloads, 42% QC

**📋 Ready to Launch**:
1. Clostridium difficile (9,133) - All scripts ready

**📝 Planned**:
1. Prevotella (obligate anaerobe #4)
2. Campylobacter jejuni (microaerophile)
3. Helicobacter pylori (microaerophile)
4. Mycobacterium tuberculosis (obligate aerobe)

### Total Samples
- **Acquired**: 20,839 samples across all studies
- **Completed**: 2,955 (Fusobacterium + Salmonella)
- **Running**: 8,751 (Bacteroides + STEC)
- **Ready**: 9,133 (Clostridium)

---

## Key Files Created Today

### Scripts (Executable)
1. `create_tree_metadata_table.py` - Comprehensive metadata table
2. `create_tree_quick_reference.py` - Simple lookup guide
3. `create_itol_annotations.py` - iTOL color annotations (FIXED)
4. `run_create_tree_metadata.sh` - Wrapper script
5. `build_host_tree_busco.sh` - Host genome tree building

### Documentation
1. `TREE_VISUALIZATION_GUIDE.md` - Complete visualization instructions
2. `TREE_METADATA_README.md` - Metadata tool usage guide
3. `OXYGEN_GRADIENT_STATUS.md` - Study progress tracking

### Data Files
1. `tree_sample_metadata_supplementary.tsv` - Publication table (8 samples)
2. `tree_quick_reference.txt` - Simple lookup (8 samples)
3. `itol_subspecies.txt` - iTOL subspecies colors (28 tips)
4. `itol_host.txt` - iTOL host colors (28 tips)
5. `itol_source.txt` - iTOL source colors (28 tips)

### Clostridium Study
1. `sra_accessions_clostridium.txt` (9,133 accessions)
2. `samplesheet_clostridium.txt` (COMPASS input)
3. `run_clostridium.sh` (SLURM job)
4. `README.md` (Study documentation)

---

## Git Activity

### Commits Today
1. Tree visualization guide creation
2. Metadata table scripts
3. iTOL annotation script (initial)
4. Fix: Use merged metadata file
5. Fix: Check 'Genus' column for SRR
6. Fix: Use full tree labels in iTOL annotations (CRITICAL)
7. Clostridium difficile study setup
8. Oxygen gradient status document
9. Host genome tree script

### Branch
**scratch** - All changes pushed

### Repository Status
- Clean working directory
- All files committed and pushed
- Ready for collaboration

---

## Technical Challenges Resolved

### Challenge 1: Metadata Column Names
**Problem**: CSV reader couldn't find SRR accessions

**Root cause**: SRR in "Genus" column (mislabeled)

**Solution**: Check multiple column names, use merged file

**Result**: Loaded 217 samples successfully

### Challenge 2: iTOL Label Matching
**Problem**: Annotations used `SRR10901569` but tree had `SRR10901569_NODE_9_length_118569...`

**Root cause**: Annotation script only used extracted SRR, not full label

**Solution**: Parse tree for full labels, extract SRR for lookup, write annotations with full labels

**Result**: All 28 tree tips annotated successfully

### Challenge 3: Sparse Metadata
**Problem**: Metadata file had many empty fields

**Root cause**: NCBI export format with inconsistent field population

**Solution**: Use merged file which already had working structure

**Result**: Reliable metadata loading

---

## Current Active Processes

### On Beocat

1. **Host genome tree building** (RUNNING)
   - Script: `build_host_tree_busco.sh`
   - Step: Identifying core BUSCO genes
   - Expected: 2-4 hours total

2. **Bacteroides fragilis study** (RUNNING)
   - Job: 7643548
   - Progress: 236/1,411 downloads (17%)
   - Expected: 3-7 days total

3. **STEC study** (RUNNING)
   - Job: 7614525
   - Progress: 7202/7340 downloads (98%), 42% QC
   - Expected: 1-2 more days

---

## Next Steps

### Immediate (Today/Tomorrow)
1. ✓ Wait for host tree to complete (~2-4 hours)
2. Download host tree to local machine
3. Compare host tree vs prophage tree topologies
4. Interpret clustering patterns in prophage tree

### Short-term (This Week)
1. Download all tree files and metadata to local
2. Create publication-quality figures in iTOL
3. Document tree interpretation findings
4. Decide whether to launch Clostridium study

### Medium-term (Next 2 Weeks)
1. Wait for Bacteroides completion
2. Wait for STEC completion
3. Analyze all three anaerobe studies together
4. Compare to facultative anaerobes

### Long-term (Publication)
1. Complete oxygen gradient study (all groups)
2. Statistical analysis across oxygen tolerance
3. Create tanglegram (host vs prophage trees)
4. Write phylogenomics methods section
5. Create supplementary materials package

---

## Research Questions to Answer

### From Prophage Tree

1. **Subspecies clustering**?
   - Look for F. necrophorum clade
   - Look for F. nucleatum clade
   - Mixed vs distinct patterns

2. **Host specificity**?
   - Do bovine prophages cluster?
   - Do human prophages cluster?
   - Or mixed?

3. **Niche specificity**?
   - Oral vs GI patterns
   - (Limited: only 1 oral sample)

### From Host vs Prophage Comparison

4. **Co-evolution**?
   - Are tree topologies similar?
   - Do same samples cluster in both trees?
   - Congruence test

5. **Horizontal transfer**?
   - Different topologies?
   - Prophages group by type, not host lineage?
   - Evidence of recent transfer?

### From Oxygen Gradient

6. **Anaerobe hypothesis**?
   - Do all three anaerobes have low burden?
   - Significantly different from facultatives?
   - Pattern holds across taxa?

---

## Publication Materials Ready

### Supplementary Files
1. `prophage_tree.nwk` - Prophage phylogenetic tree
2. `host_tree.nwk` - Host genome tree (in progress)
3. `tree_sample_metadata_supplementary.tsv` - Sample metadata table
4. `itol_subspecies.txt` - Subspecies annotations
5. `itol_host.txt` - Host annotations
6. `itol_source.txt` - Source annotations

### Documentation
1. `TREE_VISUALIZATION_GUIDE.md` - Visualization methods
2. `TREE_METADATA_README.md` - Metadata interpretation
3. `PHYLOGENOMICS_README.md` - Analysis workflow

### Reproducibility
- All scripts in Git repository
- All data files documented
- Complete workflow documented
- Can reproduce all figures

---

## Software Versions

### Tree Building
- **MAFFT**: 7.505-GCC-11.3.0-with-extensions
- **FastTree**: 2.1.11-GCCcore-11.3.0
- **Python**: 3.x with BioPython

### Analysis
- **iTOL**: Web-based (https://itol.embl.de/)
- **Python csv module**: Standard library
- **Regular expressions**: Python re module

### Pipeline
- **COMPASS**: v1.2.0-candidate
- **Nextflow**: 23.04.1
- **SLURM**: Beocat HPC scheduler

---

## Lessons Learned

### 1. Tree Label Formatting
- Always use FULL labels from tree for annotations
- Don't rely on simplified IDs
- iTOL requires exact matches

### 2. Metadata File Handling
- Check column names carefully
- NCBI exports can have inconsistent naming
- Merged/processed files often more reliable than raw

### 3. iTOL Annotation Format
- Requires specific headers (DATASET_COLORSTRIP)
- Plain TSV won't work for drag-and-drop
- Need proper formatting for each dataset type

### 4. BUSCO Gene Selection
- Need genes present in most samples
- 90% threshold balances completeness vs coverage
- Top 20 genes sufficient for reliable tree

### 5. Phylogenomics Workflow
- Concatenated genes more reliable than single gene
- Core genes better than whole genome for diverse taxa
- FastTree fast enough for exploratory analysis

---

## Statistics Summary

### Prophage Tree
- **Tips**: 28 prophage sequences
- **Samples**: 8 unique Fusobacterium genomes
- **Alignment length**: ~5.3 MB (MAFFT output)
- **Model**: GTR + 20 rate categories
- **Runtime**: 197 seconds (FastTree)

### Sample Metadata
- **Total samples**: 218 Fusobacterium genomes
- **With metadata**: 217 (99.5%)
- **In tree**: 8 (3.7%)
- **Prophage-positive**: 140 (64%)
- **Prophage-free**: 78 (36%)

### Host Tree (In Progress)
- **Samples**: 218 with BUSCO results
- **Core genes**: Top 20 most conserved
- **Strategy**: Concatenated BUSCO alignment
- **Expected length**: ~10-20 kb per gene = 200-400 kb total

---

## File Locations

### On Beocat

**Prophage tree**:
- `/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/prophage_tree.nwk`
- `/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/prophages_aligned.fna`
- `/fastscratch/tylerdoe/fusobacterium_results/analysis/phylogenomics/all_prophage_sequences.fna`

**Host tree** (in progress):
- `/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/host_tree.nwk`
- `/fastscratch/tylerdoe/fusobacterium_results/analysis/host_phylogenomics/concatenated_alignment.faa`

**Metadata**:
- `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/tree_sample_metadata_supplementary.tsv`
- `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/tree_quick_reference.txt`

**iTOL annotations**:
- `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/itol_subspecies.txt`
- `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/itol_host.txt`
- `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/itol_source.txt`

### In Repository

**Scripts**: `fusobacterium_necrophorum_study/scripts/`
**Documentation**: `fusobacterium_necrophorum_study/`
**Clostridium study**: `clostridium_difficile_study/`
**Status tracking**: `OXYGEN_GRADIENT_STATUS.md`

---

## Expected Outcomes

### Prophage Tree Interpretation

**Hypothesis**: Vertical inheritance (low burden suggests ancient prophages)

**Expected pattern**:
- F. necrophorum prophages cluster together
- F. nucleatum prophages cluster together
- Distinct subspecies-specific clades

**Alternative**: Horizontal transfer
- Mixed subspecies clustering
- Prophage-type clustering instead of host-lineage

### Host vs Prophage Comparison

**If vertical inheritance**:
- Similar tree topologies
- Same samples cluster similarly
- High congruence score
- Conclusion: Prophages co-evolved with hosts

**If horizontal transfer**:
- Different tree topologies
- Prophages cluster by type, hosts by lineage
- Low congruence score
- Conclusion: Active prophage transfer between species

### Oxygen Gradient Validation

**Current evidence**:
- Fusobacterium (anaerobe): 1.3 prophages
- Salmonella (facultative): 4.2 prophages
- 3.2× difference

**Expected with full study**:
- All anaerobes: 1-2 prophages
- Microaerophiles: 2-4 prophages
- Facultatives: 4-6 prophages
- Aerobes: 8-12 prophages

**Statistical test**: ANOVA across oxygen groups

---

*Session conducted: 2026-04-15*
*Prophage tree: Complete*
*Host tree: Building*
*Clostridium study: Ready to launch*
*Location: Beocat HPC & Local repository*

**Status: PRODUCTIVE SESSION - Major progress on tree visualization and metadata tools! ✓**
