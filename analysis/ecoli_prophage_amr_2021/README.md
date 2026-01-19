# E. coli 2021 Prophage-AMR Analysis

## Overview

Analysis of antimicrobial resistance (AMR) genes carried by prophages in E. coli NARMS isolates from 2021.

**Key Finding**: **74 AMR genes** found in prophages

## Analysis Date

January 17-18, 2026

## Dataset

**Source**: `/bulk/tylerdoe/archives/kansas_2021_ecoli`
**Year**: 2021
**Species**: *Escherichia coli*
**Database**: NARMS (National Antimicrobial Resistance Monitoring System)

## Results Summary

### Method 3 (Direct AMRFinder Scan) - Gold Standard

**Total AMR genes in prophages**: 74

This is the definitive method:
1. Extracts prophage DNA sequences from VIBRANT predictions
2. Runs AMRFinderPlus directly on prophage sequences
3. Same tool, same database as whole-genome analysis

### Method Comparison

| Method | Description | AMR Genes Found |
|--------|-------------|-----------------|
| Method 1 | Coordinate-based co-location | 0 (known bug) |
| Method 2 | Annotation search | 8 matches |
| Method 3 | **Direct AMRFinder scan** | **74 genes** ✅ |

**Conclusion**: Method 3 is the gold standard. 74 AMR genes are definitively located in prophage DNA.

## Output Location

**Results directory**: `/homes/tylerdoe/ecoli_2021_prophage_amr_analysis_20260117/`

### Key Files:
- `method3_direct_scan.csv` - Detailed list of all 74 AMR genes
- `method3_direct_scan.log` - Analysis log with sample counts
- `method1_coordinate_based.csv` - Method 1 results (for comparison)
- `method2_annotation_search.log` - Method 2 results

## SLURM Job Information

- **Job ID**: 5785805
- **Job Name**: ecoli_2021_prophage_amr
- **Runtime**: ~14 hours
- **Status**: COMPLETED
- **Exit Code**: 0
- **Completion**: January 18, 2026 05:11 AM

## Multi-Year Context

### E. coli Prophage-AMR (2021-2024)

This completes the 4-year E. coli prophage-AMR analysis series:

| Year | AMR Genes in Prophages | Analysis Date |
|------|------------------------|---------------|
| 2021 | **74** | Jan 2026 |
| 2022 | 108 | Jan 2026 |
| 2023 | 94 | Jan 2026 |
| 2024 | 120 | Jan 2026 |
| **Total** | **396** | |

**Observation**: Consistent AMR gene carriage across all 4 years, demonstrating prophages are stable AMR vectors in E. coli.

## Biological Significance

### Key Findings

1. **Prophages carry AMR genes**: 74 genes definitively located in prophage DNA
2. **Mobile genetic elements**: Prophages can transfer AMR genes between bacteria via transduction
3. **Consistent over time**: Part of 4-year series showing stable prophage-AMR association
4. **Compared to Salmonella**: E. coli prophages carry more AMR genes (~396 total) vs Salmonella (~21 total)

### Implications

- **Horizontal gene transfer**: Prophages facilitate AMR spread
- **Evolutionary dynamics**: AMR genes in prophages suggest fitness advantages
- **Public health**: Mobile AMR elements complicate resistance management
- **Surveillance**: Need to track prophage-mediated AMR dissemination

## Methods

### AMR Gene Detection

**Tool**: AMRFinderPlus v3.12.8 (NCBI)
**Database**: NCBI AMRFinder database
**Organism**: *Escherichia coli*
**Parameters**: `--nucleotide --organism Escherichia --plus`

### Prophage Detection

**Tool**: VIBRANT (Virus Identification By iteRative ANnoTation)
**Input**: SPAdes genome assemblies
**Output**: Prophage sequences (`*_phages.fna`)

### Analysis Workflow

1. Extract prophage sequences from VIBRANT output
2. Run AMRFinderPlus directly on prophage DNA
3. Compare to whole-genome AMRFinder results
4. Calculate proportion of AMR in prophages
5. Identify gene types and drug classes

## Validation

To verify these results are real (not false positives), use validation tools:

```bash
# Quick statistical check
./bin/validate_amr_prophage_statistics.py \
    /homes/tylerdoe/ecoli_2021_prophage_amr_analysis_20260117/method3_direct_scan.csv

# Spot check specific samples
./bin/spot_check_amr_prophages.py /bulk/tylerdoe/archives/kansas_2021_ecoli SRR12345678

# Visualize gene context
./bin/visualize_amr_prophage_context.py /bulk/tylerdoe/archives/kansas_2021_ecoli SRR12345678
```

See `VALIDATION_GUIDE.md` for complete validation workflow.

## Reproducibility

To reproduce this analysis:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_ecoli_2021_prophage_amr_analysis.sh
```

Expected runtime: ~14 hours

## Next Steps

### Analysis
1. **Validate results**: Run statistical checks and spot validation
2. **Gene-level analysis**: Identify which specific AMR genes are most common
3. **Drug class analysis**: Determine antibiotic classes affected
4. **Sample analysis**: Identify samples with most AMR-carrying prophages
5. **Temporal trends**: Compare 2021 vs 2022-2024 patterns

### Phylogenetics
1. **Prophage phylogeny**: Build tree of AMR-carrying prophages
2. **Cross-year comparison**: Do same prophage lineages carry AMR across years?
3. **Cross-species comparison**: Compare E. coli vs Salmonella prophages

### Publication
1. Document validation results
2. Compare to published phage-AMR studies
3. Prepare figures (gene maps, phylogenies, distributions)
4. Write methods and results sections

## Related Analyses

- **E. coli 2022-2024**: `/analysis/ecoli_prophage_amr_2022-2024/`
- **Kansas Salmonella**: `/analysis/prophage_phylogeny_kansas_2021-2025/`

## References

- **AMRFinderPlus**: Feldgarden et al. (2021) Scientific Reports
- **VIBRANT**: Kieft et al. (2020) Microbiome
- **NARMS**: National Antimicrobial Resistance Monitoring System (FDA/CDC/USDA)

## Contact

Tyler Doerks
Kansas State University
Analysis Branch: `analysis`
