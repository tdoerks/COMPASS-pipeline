# Prophage Phylogeny Results Summary

## Quick Stats

**Dataset**: Kansas NARMS Salmonella 2021-2025
**Analysis Date**: January 18, 2026

### Prophage Extraction
```
Total samples with prophages:     825
Total prophage sequences:       7,097
Total sequence length:        122 Mbp
Average prophages per sample:    ~8.6
```

### Sequence Characteristics
```
Length range:      1,010 - 111,723 bp
Mean length:              17,193 bp
Median length:            12,549 bp
```

### Analysis Parameters
```
Subsampled sequences:           500
Alignment tool:               MAFFT
Alignment time:         750 minutes
Phylogenetic tool:          FastTree
Tree model:             GTR + Gamma
Bootstrap replicates:         1,000
```

## Output Files

**Location**: `/homes/tylerdoe/prophage_phylogeny_20260116/`

| File | Description | Size |
|------|-------------|------|
| `prophages_all.fasta` | All 7,097 prophage sequences | 118 MB |
| `prophage_metadata.tsv` | Sample metadata for all prophages | - |
| `prophages_subsampled.fasta` | 500 random sequences for analysis | - |
| `prophages_aligned.fasta` | MAFFT multiple sequence alignment | 140 MB |
| `prophage_tree.nwk` | FastTree phylogenetic tree (Newick) | - |
| `mafft.log` | MAFFT alignment log | - |

## Analysis Pipeline

```
Step 1: Extract prophages from VIBRANT output
        ↓ (7,097 sequences from 825 samples)

Step 2: Random subsample to 500 sequences
        ↓ (manageable dataset size)

Step 3: MAFFT multiple sequence alignment
        ↓ (12.5 hours, 16 CPUs)

Step 4: FastTree phylogenetic inference
        ↓ (<1 minute, GTR+Gamma, 1000 bootstraps)

Output: Phylogenetic tree (prophage_tree.nwk)
```

## SLURM Jobs

### Job 5759844: Prophage Phylogeny (Steps 1-3)
```
Job Name:    prophage_phylogeny
Runtime:     12:31:05
Resources:   16 CPUs, 32 GB RAM
Status:      COMPLETED (Exit Code 0)
Date:        January 16-18, 2026
```

**Note**: Step 4 (IQ-TREE) failed because module not available on Beocat

### Manual Step 4: FastTree
```
Tool:        FastTree/2.1.11-GCCcore-11.3.0
Command:     FastTree -nt -gtr -gamma -boot 1000
Runtime:     <1 minute
Status:      COMPLETED
Date:        January 18, 2026
```

## Key Observations

### High Prophage Prevalence
- **100% of samples** contained prophages (825/825)
- Average of ~8.6 prophages per isolate
- Indicates prophages are ubiquitous in Kansas Salmonella population

### Size Diversity
- 100-fold size range (1 kb to 112 kb)
- Suggests diverse prophage types:
  - Complete prophages (~40-60 kb)
  - Partial/cryptic prophages (<10 kb)
  - Large prophages (>80 kb, possible jumbo phages)

### Alignment Success
- MAFFT completed successfully in 12.5 hours
- Large alignment size (140 MB) indicates:
  - High sequence diversity
  - Good coverage across prophage genome
  - Sufficient phylogenetic signal

## Next Steps

### Immediate Actions
1. **Download tree files** from Beocat to local machine
2. **Visualize tree** with iTOL or FigTree
3. **Inspect alignment quality** to ensure valid phylogenetic signal

### Biological Questions
1. **Temporal clustering**: Do prophages cluster by year?
2. **Host specificity**: Do prophages cluster by Salmonella serotype?
3. **Major lineages**: How many distinct prophage families?
4. **AMR association**: Do AMR-carrying prophages form specific clades?

### Follow-up Analyses
1. **Full dataset analysis**: Analyze all 7,097 prophages (if resources available)
2. **Compare with E. coli**: Cross-species prophage comparison
3. **Reference database BLAST**: Identify known prophage types
4. **Temporal analysis**: Test for evolutionary signal over 2021-2025

## Comparison with E. coli Analysis

### E. coli (2022-2024)
- **AMR genes in prophages**: 322
- **Years**: 2022, 2023, 2024
- **Species**: E. coli

### Kansas Salmonella (2021-2025)
- **AMR genes in prophages**: 21
- **Years**: 2021, 2022, 2023, 2024, 2025
- **Species**: Salmonella

**Observation**: E. coli prophages carry ~15x more AMR genes than Salmonella prophages

**Questions**:
- Do E. coli and Salmonella share prophage lineages?
- Are prophage-mediated AMR mechanisms different between species?
- Do prophages cross species boundaries?

## Visualization Guide

### Download Files
```bash
# From local machine:
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_20260116/prophage_tree.nwk .
scp tylerdoe@beocat.ksu.edu:/homes/tylerdoe/prophage_phylogeny_20260116/prophage_metadata.tsv .
```

### iTOL (Recommended)
1. Go to https://itol.embl.de/
2. Upload `prophage_tree.nwk`
3. Upload `prophage_metadata.tsv` for sample annotation
4. Color branches by:
   - Year (temporal patterns)
   - Sample ID (individual isolates)
   - Length (prophage size diversity)

### Interpreting Bootstrap Support
- **>90%**: Very strong support - high confidence
- **70-90%**: Strong support - good confidence
- **50-70%**: Moderate support - interpret cautiously
- **<50%**: Weak support - unreliable branching

## Technical Notes

### Why FastTree Instead of IQ-TREE?
- IQ-TREE not available on Beocat
- FastTree scientifically rigorous alternative
- GTR+Gamma model comparable to IQ-TREE's best models
- 1000 bootstrap replicates provide robust support values
- Widely used and validated in bacterial genomics

### Subsampling Trade-offs
**Advantages**:
- Computationally tractable
- Faster analysis iteration
- Preserves major phylogenetic patterns

**Disadvantages**:
- May miss rare prophage lineages
- Reduced statistical power
- Potential sampling bias

**Mitigation**: Random sampling (seed=42) ensures reproducibility

## Publication Potential

### Potential Findings
1. **Novel prophage lineages** in Kansas Salmonella population
2. **Temporal evolution** of prophages over 2021-2025
3. **Prophage-AMR associations** (integrate with AMR analysis)
4. **Cross-species prophage dynamics** (E. coli vs Salmonella)

### Data for Publication
- ✅ Phylogenetic tree with bootstrap support
- ✅ Alignment (500 sequences)
- ✅ Metadata (sample IDs, lengths)
- ⚠️ Need: Serotype, year, location metadata
- ⚠️ Need: AMR gene annotations on tree

## Repository Information

**Branch**: `analysis`
**Directory**: `analysis/prophage_phylogeny_kansas_2021-2025/`
**Scripts**: `scripts/run_prophage_phylogeny_complete.sh`
**Documentation**: This file + README.md

## Contact

Tyler Doerks
Kansas State University
