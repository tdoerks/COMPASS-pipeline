# E. coli Prophage-AMR Co-location Analysis (2022-2024)

## Overview

This analysis investigates whether prophages (integrated bacteriophages) carry antimicrobial resistance (AMR) genes in E. coli isolates from the National Antimicrobial Resistance Monitoring System (NARMS) across three years (2022, 2023, 2024).

**Key Finding**: Prophages DO carry AMR genes in E. coli - we identified **322 AMR genes** located within prophage regions across the three-year period.

**Note**: This is part of a 4-year series (2021-2024). See `ecoli_prophage_amr_2021/` for 2021 results (74 genes). **Combined total: 396 AMR genes** across all 4 years.

## Analysis Date

January 16, 2026

## Datasets Analyzed

| Dataset | Location | Year | Description |
|---------|----------|------|-------------|
| E. coli 2022 | `/bulk/tylerdoe/archives/kansas_2022_ecoli` | 2022 | Kansas NARMS E. coli isolates |
| E. coli 2023 | `/bulk/tylerdoe/archives/results_ecoli_2023` | 2023 | NARMS E. coli isolates |
| E. coli 2024 | `/bulk/tylerdoe/archives/results_ecoli_all_2024` | 2024 | NARMS E. coli isolates |

## Methods

Three complementary methods were used to detect AMR genes within prophage regions:

### Method 1: Coordinate-Based Co-location
- **Script**: `bin/analyze_true_amr_prophage_colocation.py`
- **Approach**: Compares genomic coordinates of AMR genes (from AMRFinderPlus) with prophage region coordinates (from VIBRANT)
- **Status**: ⚠️ Known bug - consistently reports 0 genes (coordinate matching issue)

### Method 2: Annotation Search
- **Script**: `bin/search_amr_in_vibrant_annotations.py`
- **Approach**: Searches VIBRANT prophage annotation files for AMR-related keywords
- **Status**: Limited sensitivity - depends on prophage annotation quality

### Method 3: Direct AMRFinder Scan ✅ (Gold Standard)
- **Script**: `bin/run_amrfinder_on_prophages.py`
- **Approach**: Extracts prophage DNA sequences and directly scans them with AMRFinderPlus
- **Status**: Most reliable method - provides definitive AMR gene identification

## Results Summary

| Year | AMR Genes in Prophages | Method Used |
|------|------------------------|-------------|
| 2022 | 108 | Direct Scan (Method 3) |
| 2023 | 94 | Direct Scan (Method 3) |
| 2024 | 120 | Direct Scan (Method 3) |
| **Total** | **322** | |

### Method Comparison

| Method | E. coli 2022 | E. coli 2023 | E. coli 2024 | Total |
|--------|--------------|--------------|--------------|-------|
| Method 1 (Coordinate) | 0 | 0 | 0 | 0 |
| Method 2 (Annotation) | Not complete | Not complete | Not complete | - |
| Method 3 (Direct Scan) | 108 | 94 | 120 | 322 |

## Output Locations

### Analysis Results
All results are stored in: `/homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/`

Directory structure:
```
ecoli_prophage_amr_analysis_20260116/
├── ecoli_2022/
│   ├── method1_coordinate_based.csv
│   ├── method2_annotation_search.log
│   └── method3_direct_scan.log
├── ecoli_2023/
│   ├── method1_coordinate_based.csv
│   ├── method2_annotation_search.log
│   └── method3_direct_scan.log
├── ecoli_2024/
│   ├── method1_coordinate_based.csv
│   ├── method2_annotation_search.log
│   └── method3_direct_scan.log
└── summary.log
```

### SLURM Job Information
- **Job ID**: 5758750
- **Job Name**: ecoli_prophage_amr
- **Runtime**: 1 day, 7 minutes, 16 seconds
- **Status**: COMPLETED
- **Exit Code**: 0

## Biological Significance

These findings demonstrate that:

1. **Prophages are mobile AMR vectors**: Prophages can transfer AMR genes between bacteria through transduction
2. **Consistent over time**: AMR-carrying prophages are present across multiple years (2022-2024)
3. **Significant prevalence**: 322 AMR genes in prophages represents a substantial mobile resistome

## Scripts Used

### Main Analysis Script
- `run_ecoli_prophage_amr_analysis.sh` - Master script that runs all three methods on all datasets

### Supporting Analysis Scripts
Located in `bin/`:
- `analyze_true_amr_prophage_colocation.py` - Method 1 (coordinate-based)
- `search_amr_in_vibrant_annotations.py` - Method 2 (annotation search)
- `run_amrfinder_on_prophages.py` - Method 3 (direct scan)

## Reproducibility

To reproduce this analysis:

```bash
# Ensure you're in the COMPASS-pipeline directory
cd /homes/tylerdoe/COMPASS-pipeline

# Load required modules
module load AMRFinderPlus

# Run the analysis
sbatch run_ecoli_prophage_amr_analysis.sh
```

The script will:
1. Create timestamped output directory
2. Run all three methods on each dataset
3. Generate summary statistics
4. Save detailed CSV files with gene-level information

## Known Issues

### Method 1 Bug
The coordinate-based method (Method 1) has a bug that prevents it from correctly identifying overlapping genomic coordinates. This needs investigation and fixing.

**Evidence**:
- Method 1 reports 0 genes across all datasets
- Method 3 (direct scan) finds 322 genes
- Method 3 is definitive (extracts and scans actual DNA)

**Recommendation**: Use Method 3 results as ground truth until Method 1 is fixed.

## Next Steps

1. **Fix Method 1**: Debug coordinate matching logic
2. **Gene-level analysis**: Examine which specific AMR genes are most common in prophages
3. **Drug class analysis**: Determine which antibiotic classes are affected
4. **Sample-level analysis**: Identify which E. coli samples have the most AMR-carrying prophages
5. **Temporal trends**: Compare AMR gene prevalence across years
6. **Phylogenetic analysis**: Examine evolutionary relationships of AMR-carrying prophages

## References

- **COMPASS Pipeline**: Comprehensive Omics Analysis of Salmonella and Phages
- **AMRFinderPlus**: NCBI's antimicrobial resistance gene database and detection tool
- **VIBRANT**: Virus Identification By iteRative ANnoTation - prophage detection tool
- **NARMS**: National Antimicrobial Resistance Monitoring System (FDA/CDC/USDA)

## Contact

Tyler Doerks
Kansas State University
Branch: analysis/ecoli-prophage-amr-2022-2024
