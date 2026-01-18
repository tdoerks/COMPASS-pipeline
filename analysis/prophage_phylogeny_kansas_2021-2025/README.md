# Prophage Phylogenetic Analysis - Kansas NARMS 2021-2025

## Overview

This analysis constructs a phylogenetic tree of prophages (integrated bacteriophages) from Kansas NARMS Salmonella isolates spanning 2021-2025. The goal is to understand evolutionary relationships, temporal patterns, and potential host-specificity of prophages in this population.

## Analysis Date

January 18, 2026

## Dataset

**Source**: `/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod`

**Samples**: 825 samples with prophage data
**Total prophages extracted**: 7,097 prophage sequences
**Total size**: 122 Mbp
**Length range**: 1,010 - 111,723 bp
**Mean length**: 17,193 bp
**Median length**: 12,549 bp

## Methods

### Step 1: Prophage Sequence Extraction
- **Tool**: Python with BioPython
- **Input**: VIBRANT prophage predictions (`*_phages.fna`)
- **Output**: Multi-FASTA with all prophage sequences
- **Result**: 7,097 prophages from 825 samples

### Step 2: Subsampling
- **Reason**: 7,097 sequences too large for phylogenetic analysis
- **Method**: Random subsampling (seed=42)
- **Target**: 500 sequences (manageable for alignment/tree building)
- **Tool**: Python BioPython SeqIO

### Step 3: Multiple Sequence Alignment
- **Tool**: MAFFT v7.505
- **Algorithm**: Auto mode (automatically selects best strategy)
- **Threads**: 16 CPUs
- **Runtime**: 750 minutes (~12.5 hours)
- **Input**: 500 subsampled prophage sequences
- **Output**: 140 MB aligned FASTA

### Step 4: Phylogenetic Tree Construction
- **Tool**: FastTree v2.1.11 (IQ-TREE not available on Beocat)
- **Model**: GTR+Gamma (Generalized Time-Reversible with gamma rate variation)
- **Bootstrap**: 1,000 replicates (SH-like support)
- **Runtime**: <1 minute (FastTree is very fast!)
- **Output**: Newick format tree file

## SLURM Job Information

### Initial Job (Steps 1-3)
- **Job ID**: 5759844
- **Job Name**: prophage_phylogeny
- **Runtime**: 12:31:05
- **Status**: COMPLETED
- **Exit Code**: 0
- **Note**: Step 4 failed due to IQ-TREE not being available

### Tree Building (Step 4)
- **Method**: Manual execution with FastTree
- **Module**: FastTree/2.1.11-GCCcore-11.3.0
- **Date**: January 18, 2026
- **Status**: COMPLETED

## Output Files

All outputs located in: `/homes/tylerdoe/prophage_phylogeny_20260116/`

```
prophage_phylogeny_20260116/
├── prophages_all.fasta              (7,097 sequences - all prophages)
├── prophage_metadata.tsv            (Sample metadata for all prophages)
├── prophages_subsampled.fasta       (500 sequences - subsampled for analysis)
├── prophages_aligned.fasta          (500 sequences - MAFFT alignment, 140 MB)
├── prophage_tree.nwk                (Phylogenetic tree - Newick format)
└── mafft.log                        (MAFFT alignment log)
```

## Key Findings

### Dataset Characteristics
- **High prophage prevalence**: 825/825 samples (100%) contained prophages
- **Multiple prophages per sample**: Average ~8.6 prophages per isolate
- **Size diversity**: 100-fold size range suggests diverse prophage types

### Phylogenetic Analysis
- **Tree structure**: To be visualized and interpreted
- **Bootstrap support**: 1,000 replicates for branch confidence
- **Evolutionary model**: GTR+Gamma accounts for nucleotide substitution patterns

## Next Steps

### 1. Tree Visualization
Download and visualize the tree:

```bash
# Download tree from Beocat
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_20260116/prophage_tree.nwk .
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_20260116/prophage_metadata.tsv .
```

**Visualization options:**
- **iTOL** (recommended): https://itol.embl.de/ - Interactive, publication-quality
- **FigTree**: Desktop application for tree exploration
- **R ggtree**: Programmatic visualization with ggplot2
- **Python ETE3**: Scriptable tree rendering

### 2. Biological Questions to Explore

**Temporal patterns:**
- Do prophages from the same year cluster together?
- Is there evidence of prophage evolution/drift over 2021-2025?

**Host specificity:**
- Do prophages cluster by Salmonella serotype?
- Are certain prophage lineages serotype-specific?

**Geographic patterns:**
- Do Kansas prophages form distinct clusters?
- Evidence of local vs. imported prophage populations?

**AMR associations:**
- Cross-reference with AMR-carrying prophages (from E. coli analysis)
- Do AMR-prophages share common ancestry?

### 3. Statistical Analyses

- **Root-to-tip regression**: Test for temporal signal
- **Phylogenetic diversity metrics**: Alpha/beta diversity across years
- **Clade annotation**: Identify major prophage lineages
- **Host-phylogeny correlation**: Test for prophage-host co-evolution

### 4. Comparative Analysis

Compare Kansas Salmonella prophages with:
- E. coli prophages (from ecoli_prophage_amr analysis)
- Reference prophage databases (PHASTER, IMG/VR)
- Published Salmonella prophage studies

## Reproducibility

To reproduce this analysis:

```bash
# Navigate to pipeline directory
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Submit SLURM job
sbatch run_prophage_phylogeny_complete.sh
```

The script will:
1. Extract all prophage sequences from VIBRANT output
2. Subsample to 500 sequences if dataset is large
3. Perform MAFFT alignment
4. Attempt IQ-TREE (will fail on Beocat)

Then manually run FastTree:
```bash
module load FastTree/2.1.11-GCCcore-11.3.0
FastTree -nt -gtr -gamma -boot 1000 prophages_aligned.fasta > prophage_tree.nwk
```

## Technical Notes

### Tool Selection: FastTree vs IQ-TREE

**IQ-TREE** (originally planned):
- More sophisticated model selection (MFP)
- Ultrafast bootstrap
- Better for publication
- **Not available on Beocat**

**FastTree** (used):
- Very fast (minutes vs hours)
- GTR+Gamma model comparable to IQ-TREE
- SH-like support values (similar to bootstrap)
- Well-validated for bacterial genomics
- **Available on Beocat**

**Conclusion**: FastTree is scientifically rigorous and appropriate for this analysis.

### Subsampling Strategy

Why subsample to 500 sequences?
- Computational tractability (alignment of 7,000 sequences impractical)
- Sufficient for detecting major phylogenetic patterns
- Random sampling preserves diversity
- Can analyze full dataset if needed with more resources

**Potential bias**: Random sampling may miss rare prophage lineages

### Alignment Quality

- MAFFT auto mode selects optimal algorithm based on dataset size
- 750 minutes for 500 sequences is reasonable
- Large alignment size (140 MB) suggests high diversity or long sequences
- Should verify alignment quality before interpreting tree

## Integration with Other Analyses

### Link to AMR Analysis
- E. coli prophages carry 322 AMR genes (from `ecoli_prophage_amr_2022-2024/`)
- Kansas Salmonella prophages carry 21 AMR genes
- **Question**: Do AMR-carrying prophages share phylogenetic relationships?

### Cross-Species Comparison
- Compare Salmonella prophage tree with E. coli prophage tree
- Identify prophage lineages that cross species boundaries
- Evidence for broad host range vs specialist prophages

## References

### Tools
- **MAFFT**: Katoh & Standley (2013) Mol Biol Evol 30:772-780
- **FastTree**: Price et al. (2010) PLoS ONE 5(3):e9490
- **VIBRANT**: Kieft et al. (2020) Microbiome 8:124
- **BioPython**: Cock et al. (2009) Bioinformatics 25:1422-1423

### COMPASS Pipeline
- **Pipeline**: COMPASS v1.3-dev
- **Repository**: https://github.com/tdoerks/COMPASS-pipeline
- **Branch**: analysis

## Contact

Tyler Doerks
Kansas State University
Analysis Branch: analysis/prophage_phylogeny_kansas_2021-2025
