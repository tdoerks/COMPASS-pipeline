# COMPASS Pipeline - Accession List Tools

This document explains how to create custom SRA accession lists for the COMPASS pipeline when the built-in metadata filtering isn't sufficient.

## When to Use Accession List Tools

### ✅ Use Custom Accession Lists When You Need:

- **Monthly/quarterly sampling** (e.g., "100 E. coli per month from 2020-2026")
- **Balanced temporal distribution** (e.g., "equal samples from each year")
- **Complex sampling strategies** (e.g., "50 clinical + 50 environmental per state")
- **Pre-filtered datasets** (e.g., "only high-quality assemblies")
- **Reproducible random sampling** (set random seed for consistency)
- **Multi-organism studies** with different sampling rates per organism

### ❌ Use Built-in Metadata Filtering When You Need:

- **All samples from a year/year range** (e.g., "all Kansas 2023 data")
- **Simple organism filtering** (e.g., "all Salmonella from 2020-2024")
- **Platform filtering** (e.g., "only Illumina data")
- **Geographic filtering** (e.g., "only Kansas samples")
- **Library source filtering** (e.g., "only GENOMIC isolates")

## Quick Start - Interactive Generator

The easiest way to create a custom accession list is using the interactive generator:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
python3 generate_accession_list.py
```

It will ask you simple questions:
1. **Organism** (e.g., Escherichia coli)
2. **Time period** (start year, end year)
3. **Sampling strategy** (monthly, yearly, all)
4. **Platform** (Illumina, PacBio, Nanopore, Any)
5. **Library source** (GENOMIC, METAGENOMIC, Any)
6. **Geographic filter** (optional)

### Example Session

```
=======================================================================
  COMPASS Pipeline - Interactive Accession List Generator
=======================================================================

1. What organism do you want to study?
   Examples: Escherichia coli, Salmonella, Klebsiella pneumoniae
Organism [Escherichia coli]: Salmonella

2. What time period?
Start year [2020]: 2022
End year [2026]: 2024

3. What sampling strategy?
   1) Monthly (X samples per month)
   2) Yearly (X samples per year)
   3) All available
Choice [1]: 1
Samples per month [100]: 50

4. What sequencing platform?
   Options: Illumina, PacBio, Nanopore, Any
Platform [Illumina]:

5. What library source?
   Options: GENOMIC, METAGENOMIC, TRANSCRIPTOMIC, Any
Library source [GENOMIC]:

6. Geographic location filter (optional)
   Examples: KS, USA, China, or leave blank for all
Geographic filter [none]:

=======================================================================
Generating files...
=======================================================================

✓ Generated files:
  1. fetch_salmonella_monthly_50_2022-2024.py
  2. run_salmonella_monthly_2022-2024.sh

Summary:
  Organism: Salmonella
  Period: 2022 - 2024
  Strategy: Monthly
  Samples per period: 50
  Estimated total: ~1800 samples
  Runtime: ~36 minutes (1 sec per API call)

Next steps:
  1. python3 fetch_salmonella_monthly_50_2022-2024.py
  2. sbatch run_salmonella_monthly_2022-2024.sh
```

## How It Works

### Step 1: Generate Scripts

The interactive tool creates two files:

1. **Python fetcher script** (`fetch_*.py`)
   - Queries NCBI SRA database using E-utilities API
   - Applies your filters (organism, date, platform, etc.)
   - Samples N random accessions per time period
   - Saves to text file (one SRR accession per line)

2. **SLURM submission script** (`run_*.sh`)
   - Pre-configured to use the accession list
   - Sets up proper working directories
   - Configures COMPASS pipeline parameters

### Step 2: Fetch Accessions

```bash
python3 fetch_*.py
```

- Takes 5-60 minutes depending on time range
- Rate-limited to 1 query per second (NCBI policy)
- Progress shown in real-time
- Output: `sra_accessions_*.txt`

### Step 3: Run Pipeline

```bash
sbatch run_*.sh
```

- Submits COMPASS pipeline job to SLURM
- Uses the accession list as input
- Processes all samples with full COMPASS workflow

## Manual Accession Lists

If you have accessions from another source (e.g., a publication, collaborator, or previous study), create a text file:

```bash
# sra_accessions_my_study.txt
SRR12345678
SRR12345679
SRR12345680
...
```

Then run the pipeline:

```bash
nextflow run main.nf \
    --input_mode sra_list \
    --input sra_accessions_my_study.txt \
    --outdir results_my_study \
    -profile beocat
```

## Advanced Examples

### Example 1: Temporal Trends Study

**Goal**: Study E. coli evolution over 10 years with balanced monthly sampling

```bash
python3 generate_accession_list.py
# Organism: Escherichia coli
# Start: 2015
# End: 2025
# Strategy: Monthly
# Samples per month: 50
# Platform: Illumina
# Source: GENOMIC
```

**Result**: ~6,600 E. coli samples (132 months × 50 samples)

### Example 2: Multi-Organism Comparison

**Goal**: Compare prophage content across 3 organisms

Create 3 separate lists:

```bash
# 1. E. coli
python3 generate_accession_list.py
# Output: fetch_ecoli_yearly_500_2020-2024.py

# 2. Salmonella
python3 generate_accession_list.py
# Output: fetch_salmonella_yearly_500_2020-2024.py

# 3. Klebsiella
python3 generate_accession_list.py
# Output: fetch_klebsiella_yearly_500_2020-2024.py
```

Then combine or run separately:

```bash
# Option 1: Combine lists
cat sra_accessions_*.txt > sra_accessions_combined.txt

# Option 2: Run separate pipelines
sbatch run_ecoli_yearly_2020-2024.sh
sbatch run_salmonella_yearly_2020-2024.sh
sbatch run_klebsiella_yearly_2020-2024.sh
```

### Example 3: Geographic Comparison

**Goal**: Compare AMR patterns between Kansas and California E. coli

```bash
# Kansas samples
python3 generate_accession_list.py
# Geographic filter: KS
# Output: fetch_escherichia_coli_monthly_100_2020-2024.py

# Rename output
mv fetch_escherichia_coli_monthly_100_2020-2024.py fetch_ecoli_ks_monthly_100.py

# California samples
python3 generate_accession_list.py
# Geographic filter: CA
# Rename similarly
```

## Customizing Generated Scripts

The generated Python scripts are fully editable. Common customizations:

### 1. Change Random Seed (for reproducibility)

```python
# Add at top of main()
random.seed(42)  # Same samples every time
```

### 2. Add Quality Filters

```python
# In the search term
params = {
    'term': f'{organism}[Organism] AND {date_str}[Release Date] AND "high quality"[Filter]',
    ...
}
```

### 3. Adjust Sample Size by Month

```python
# Instead of fixed samples_per_period
if month in [6, 7, 8]:  # Summer months
    sample_size = 200
else:
    sample_size = 50
```

## Troubleshooting

### Problem: "No accessions found"

**Cause**: Filters too restrictive or no data for that period

**Solution**:
- Broaden filters (use "Any" for platform/source)
- Check NCBI manually: https://www.ncbi.nlm.nih.gov/sra/
- Adjust date range

### Problem: Script takes too long

**Cause**: Too many time periods or large sample size

**Solution**:
- Reduce samples per period
- Use yearly instead of monthly sampling
- Run as background job: `nohup python3 fetch_*.py &`

### Problem: NCBI API errors

**Cause**: Rate limiting or network issues

**Solution**:
- Script has built-in delays (1 sec between queries)
- Wait a few minutes and re-run
- Check internet connection

## Tips for Efficient Sampling

1. **Start small**: Test with 1 year before doing 10 years
2. **Check availability**: Use NCBI website to verify data exists
3. **Balance coverage**: Monthly sampling better than yearly for trends
4. **Document your strategy**: Save the generator output for reproducibility
5. **Version control**: Commit generated scripts to git with descriptive names

## Comparison: Built-in vs. Custom Lists

| Feature | Built-in Filtering | Custom Accession Lists |
|---------|-------------------|------------------------|
| Ease of use | ✓ Very easy | Moderate (interactive tool helps) |
| Temporal sampling | Year ranges only | Month/quarter/custom |
| Random sampling | No | Yes, with seed control |
| Sample limits | All matching data | Precise N per period |
| Reproducibility | Good | Excellent (save list) |
| Multiple organisms | Sequential only | Can combine lists |
| Geographic control | Basic | Precise |

## Getting Help

- **Tool issues**: Check script comments and error messages
- **NCBI API**: https://www.ncbi.nlm.nih.gov/books/NBK25500/
- **COMPASS pipeline**: See main README.md
- **Examples**: See `fetch_ecoli_monthly_v2.py` for working example

## Credits

Interactive generator and documentation created January 2026 for the COMPASS pipeline.

Based on real-world use case: "100 E. coli per month from 2020-2026" sampling strategy.
