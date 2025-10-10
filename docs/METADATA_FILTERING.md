# NARMS Metadata Filtering Guide

The COMPASS pipeline provides comprehensive filtering options for NARMS metadata to help you select specific subsets of samples for analysis.

## Overview

The pipeline automatically downloads metadata from three NARMS BioProjects:
- **PRJNA292664**: Campylobacter
- **PRJNA292661**: Salmonella
- **PRJNA292663**: E. coli

You can then apply various filters to select only the samples you're interested in analyzing.

## Quick Start

### Example 1: Filter by State and Year
```bash
nextflow run main.nf \
    -profile beocat \
    --filter_state "KS" \
    --filter_year_start 2020 \
    --filter_year_end 2023
```

### Example 2: Filter by Host and Source
```bash
nextflow run main.nf \
    -profile beocat \
    --filter_host "chicken,turkey" \
    --filter_isolation_source "cecum,carcass"
```

### Example 3: Clinical Samples Only
```bash
nextflow run main.nf \
    -profile beocat \
    --filter_sample_type "clinical" \
    --filter_isolation_source "blood,urine"
```

## Available Filters

### Geographic Filters

#### `--filter_state`
Filter by US state code embedded in sample names.

**Format**: Two-letter state code
**Example**: `--filter_state "KS"` (Kansas)
**Pattern matched**: Sample names like `19KS07`, `20KS123`

**Common state codes**:
- KS = Kansas
- CA = California
- TX = Texas
- NY = New York
- FL = Florida

#### `--filter_geography`
Filter by geographic location in metadata fields.

**Format**: Single location or comma-separated list
**Example**: `--filter_geography "Kansas,Missouri"`
**Supports**: Partial matching, case-insensitive

**Metadata fields searched**:
- `geo_loc_name`
- `geographic_location`
- `collection_location`
- Sample names and library names

### Temporal Filters

#### `--filter_year_start`
Minimum year (inclusive).

**Format**: Four-digit year
**Example**: `--filter_year_start 2020`
**Uses**: `ReleaseDate` field from metadata

#### `--filter_year_end`
Maximum year (inclusive).

**Format**: Four-digit year
**Example**: `--filter_year_end 2023`
**Uses**: `ReleaseDate` field from metadata

### Biological Filters

#### `--filter_host`
Filter by host organism.

**Format**: Single host or comma-separated list
**Example**: `--filter_host "chicken,turkey,swine"`
**Supports**: Partial matching, case-insensitive

**Common hosts**:
- chicken
- turkey
- swine (pig)
- cattle (cow)
- human

**Metadata fields searched**:
- `host`
- `Host`
- `host_subject_id`

#### `--filter_isolation_source`
Filter by isolation source (body site or sample origin).

**Format**: Single source or comma-separated list
**Example**: `--filter_isolation_source "cecum,carcass,feces"`
**Supports**: Partial matching, case-insensitive

**Common sources**:
- cecum
- carcass
- feces / fecal
- blood
- urine
- meat
- retail
- environmental

**Metadata fields searched**:
- `isolation_source`
- `Isolation_source`
- Sample names and library names

#### `--filter_sample_type`
Filter by sample type classification.

**Format**: Single type or comma-separated list
**Example**: `--filter_sample_type "clinical,environmental"`
**Supports**: Partial matching, case-insensitive

**Common types**:
- clinical
- environmental
- food
- veterinary

**Metadata fields searched**:
- `sample_type`
- `SampleType`
- Sample names and library names

### General Filter

#### `--filter_source`
General source filter (backward compatibility).

**Format**: Single pattern
**Example**: `--filter_source "chicken"`
**Supports**: Partial matching, case-insensitive

**Note**: If `--filter_isolation_source` is specified, this parameter is ignored.

**Metadata fields searched**:
- `isolation_source`
- `host`
- Sample names and library names

## Filter Combinations

All filters are applied using **AND logic** - samples must match ALL specified filters.

### Example: Kansas Chicken Samples from 2020-2023
```bash
nextflow run main.nf \
    -profile beocat \
    --filter_state "KS" \
    --filter_host "chicken" \
    --filter_year_start 2020 \
    --filter_year_end 2023
```

### Example: Clinical Samples from Multiple States
```bash
nextflow run main.nf \
    -profile beocat \
    --filter_geography "Kansas,Missouri,Nebraska" \
    --filter_sample_type "clinical" \
    --filter_isolation_source "blood,csf"
```

### Example: Retail Meat Samples
```bash
nextflow run main.nf \
    -profile beocat \
    --filter_isolation_source "retail,meat,chicken breast" \
    --filter_sample_type "food"
```

## Multiple Values

Several filters support comma-separated lists to match multiple values using **OR logic**:

- `--filter_host`: Match any of the specified hosts
- `--filter_isolation_source`: Match any of the specified sources
- `--filter_geography`: Match any of the specified locations
- `--filter_sample_type`: Match any of the specified types

**Example**: Samples from chickens OR turkeys
```bash
--filter_host "chicken,turkey"
```

**Example**: Blood OR urine samples
```bash
--filter_isolation_source "blood,urine"
```

## Output Files

After filtering, the following files are generated in `results/filtered_samples/`:

### `filtered_samples.csv`
Complete metadata for all samples that passed filters.

**Contains**: All original metadata columns plus `organism` column

### `srr_accessions.txt`
List of SRR accessions (one per line) for all filtered samples.

**Use**: Input for batch download scripts

### `{organism}_srr_list.txt`
Pathogen-specific SRR lists (e.g., `campylobacter_srr_list.txt`).

**Generated for**: Each pathogen with >0 samples

### `filter_summary.txt`
Human-readable summary of filtering results.

**Example**:
```
NARMS Metadata Filtering Summary
============================================================

Applied Filters:
------------------------------------------------------------
  State: KS
  Year start: 2020
  Year end: 2023
  Host: chicken

Campylobacter (campylobacter):
  Initial samples: 15234
  State filter (KS): 342
  Year >= 2020: 198
  Year <= 2023: 198
  Host filter (chicken): 156
  Final: 156 samples (1.0% retained)

Salmonella (salmonella):
  Initial samples: 23451
  State filter (KS): 521
  Year >= 2020: 289
  Year <= 2023: 289
  Host filter (chicken): 203
  Final: 203 samples (0.9% retained)

============================================================

TOTAL FILTERED SAMPLES: 359
  Campylobacter: 156
  Salmonella: 203
```

## Filter Validation

### No Samples Match Filters
If no samples pass your filters, the pipeline will:
1. Print a warning to the log
2. Generate empty output files
3. Include error message in `filter_summary.txt`

**Solution**: Relax filters or check filter values for typos

### Very Few Samples
If <5% of samples pass filters, review:
- State code formatting (must be 2 letters)
- Year range validity
- Host/source spelling
- Whether filters are too restrictive

## Tips and Best Practices

### 1. Start Broad, Then Narrow
```bash
# First run: See what's available
nextflow run main.nf -profile beocat --filter_state "KS"

# Check filter_summary.txt to see sample counts

# Second run: Add more specific filters
nextflow run main.nf -profile beocat \
    --filter_state "KS" \
    --filter_host "chicken" \
    --filter_year_start 2020
```

### 2. Use Partial Matching
Filters use substring matching, so:
- `"chicken"` matches "chicken", "Chicken", "chicken breast"
- `"fec"` matches "feces", "fecal", "fecal swab"

### 3. Check Metadata First
Download and examine raw metadata to see available values:
```bash
# Run metadata download only
nextflow run main.nf -profile beocat -entry DOWNLOAD_NARMS_METADATA

# Examine metadata
head -n 20 results/metadata/campylobacter_metadata.csv
```

### 4. Combine Geographic Filters
Use both `filter_state` and `filter_geography` for more precise location matching:
```bash
--filter_state "KS" \
--filter_geography "Manhattan,Wichita"
```

### 5. Test with Small Subsets
Add year filters to create smaller test datasets:
```bash
--filter_year_start 2023 \
--filter_year_end 2023
```

## Advanced Usage

### Exclude Specific Patterns
To exclude samples, use negative patterns in custom configs:
```groovy
// In custom.config
params {
    filter_isolation_source = "chicken"
    // Then manually remove unwanted samples from filtered_samples.csv
}
```

### Combine with Custom Samplesheets
1. Run metadata filtering to get `filtered_samples.csv`
2. Edit CSV to add/remove specific samples
3. Convert to samplesheet format
4. Run pipeline with custom samplesheet

### Automate Filtering Workflows
Create shell scripts for common filter combinations:

```bash
#!/bin/bash
# filter_kansas_chicken.sh

nextflow run main.nf \
    -profile beocat \
    --filter_state "KS" \
    --filter_host "chicken" \
    --filter_year_start 2020 \
    --outdir "results/ks_chicken_2020plus"
```

## Troubleshooting

### Filter Not Working
**Check**:
1. Parameter syntax: `--filter_host "chicken"` (two dashes, quotes for values with spaces)
2. Spelling and case (filters are case-insensitive but must be spelled correctly)
3. Field availability in metadata (not all fields present for all samples)

### Unexpected Sample Counts
**Review**:
1. `filter_summary.txt` shows step-by-step filtering
2. Check raw metadata for actual field values
3. Verify filter logic (AND between filters, OR within comma-separated lists)

### Missing Organism
**Cause**: All samples for that organism were filtered out
**Solution**: Check if filters are too restrictive for that pathogen

## Contact

For questions or issues with metadata filtering:
- Open an issue: https://github.com/tdoerks/COMPASS-pipeline/issues
- Include your filter parameters and `filter_summary.txt`
