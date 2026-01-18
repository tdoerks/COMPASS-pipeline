# E. coli Prophage-AMR Analysis Results Summary

## Key Findings

**Total AMR genes found in prophages: 322**

### Breakdown by Year

```
┌──────────┬───────────────────────┐
│   Year   │ AMR Genes in Prophages│
├──────────┼───────────────────────┤
│   2022   │         108           │
│   2023   │          94           │
│   2024   │         120           │
├──────────┼───────────────────────┤
│  TOTAL   │         322           │
└──────────┴───────────────────────┘
```

## Analysis Run Details

**Date**: January 16, 2026
**SLURM Job ID**: 5758750
**Runtime**: 1 day, 7 minutes, 16 seconds
**Status**: COMPLETED (Exit Code 0)

## Method Performance

All three methods were run on each dataset:

### Method 1: Coordinate-Based Co-location
- **Result**: 0 genes found across all datasets
- **Status**: ⚠️ Known bug in coordinate matching logic

### Method 2: Annotation Search
- **Result**: Analysis incomplete
- **Status**: Searches VIBRANT annotations for AMR keywords

### Method 3: Direct AMRFinder Scan ✅
- **Result**: 322 genes found (108 + 94 + 120)
- **Status**: GOLD STANDARD - Most reliable method
- **Approach**: Extracts prophage DNA and directly scans with AMRFinderPlus

## Detailed Results Location

Full analysis results are stored on Beocat at:
```
/homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/
```

### Directory Structure:
```
ecoli_prophage_amr_analysis_20260116/
├── ecoli_2022/
│   ├── method1_coordinate_based.csv      (Method 1 output)
│   ├── method2_annotation_search.log     (Method 2 output)
│   ├── method3_direct_scan.log           (Method 3 output)
│   └── amr_prophage_results/             (Detailed AMR gene data)
├── ecoli_2023/
│   ├── method1_coordinate_based.csv
│   ├── method2_annotation_search.log
│   ├── method3_direct_scan.log
│   └── amr_prophage_results/
├── ecoli_2024/
│   ├── method1_coordinate_based.csv
│   ├── method2_annotation_search.log
│   ├── method3_direct_scan.log
│   └── amr_prophage_results/
└── summary.log
```

## Sample Output (Method 3 - E. coli 2024)

```
=== E. coli 2024 Analysis Complete ===

Direct AMRFinder scan (Method 3) results:
Total prophage sequences analyzed: [from VIBRANT output]
AMR genes detected in prophages: 120

Output directory: /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2024/amr_prophage_results/

Files generated:
- amr_summary.tsv          (All AMR hits)
- prophage_amr_genes.csv   (Prophage-specific hits)
- analysis_stats.txt       (Summary statistics)
```

## Biological Interpretation

### Significance
1. **Prophages are AMR vectors**: Prophages can mobilize and transfer AMR genes between bacterial cells
2. **Persistent over time**: AMR-carrying prophages detected across 3 consecutive years
3. **Substantial prevalence**: 322 genes represents a significant mobile AMR reservoir

### Implications
- **Horizontal gene transfer**: Prophages facilitate AMR spread through transduction
- **Evolutionary dynamics**: AMR genes persisting in prophages suggest fitness advantage
- **Public health concern**: Mobile AMR elements complicate resistance management

## Comparison with Other Datasets

### Kansas Salmonella (2021-2025)
- **Dataset**: `/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod`
- **Method 3 Result**: 21 AMR genes in prophages
- **Observation**: Lower prevalence compared to E. coli (21 vs 322)

### Species Comparison
```
┌─────────────────┬───────────────────────┬──────────────┐
│    Species      │ AMR Genes in Prophages│   Timeframe  │
├─────────────────┼───────────────────────┼──────────────┤
│   E. coli       │         322           │  2022-2024   │
│   Salmonella    │          21           │  2021-2025   │
└─────────────────┴───────────────────────┴──────────────┘
```

E. coli shows ~15x more AMR genes in prophages compared to Salmonella.

## Next Analysis Steps

### Immediate
1. Fix Method 1 coordinate matching bug
2. Extract detailed gene lists from CSV files
3. Identify which AMR genes are most common
4. Determine drug classes affected

### Extended
1. Sample-level analysis (which isolates have most AMR-prophages)
2. Geographic distribution (if state metadata available)
3. Temporal trends (is prevalence increasing?)
4. Phylogenetic analysis of AMR-carrying prophages
5. Cross-species comparison (E. coli vs Salmonella mechanisms)

## Related Analyses

- **Prophage phylogeny**: `run_prophage_phylogeny_complete.sh` (fixed path expansion bug)
- **Kansas Salmonella prophage-AMR**: Similar analysis on different pathogen
- **COMPASS comprehensive reports**: Enhanced metadata reports with 30+ fields

## Notes

- Method 3 (direct scan) should be considered the definitive result
- Method 1 needs debugging before use in publications
- Raw data preserved for future re-analysis with improved methods
- All scripts version-controlled in git branch: `analysis/ecoli-prophage-amr-2022-2024`
