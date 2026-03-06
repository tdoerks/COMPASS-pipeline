# Kansas 2021-2025 NARMS Analysis Guide

## Overview

This guide explains how to run AMR-prophage analysis on your Kansas 2021-2025 NARMS dataset located at:
```
/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/
```

## What the Analysis Does

The analysis scripts investigate the relationship between **antimicrobial resistance (AMR) genes** and **prophages** in your bacterial genomes. Key analyses include:

1. **Gene Enrichment**: Which AMR genes show highest % on prophage contigs?
2. **Deep Dive**: Detailed characteristics of AMR genes on prophage contigs
3. **Specific Investigations**: dfrA51 (trimethoprim resistance), mdsA+mdsB co-occurrence
4. **Comprehensive Report**: Combined HTML report with all findings
5. **Mobile Elements**: Associations with plasmids, integrases, transposases

## Quick Start

### Step 1: Check if your data has required files

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
bash prepare_analysis_data.sh
```

This will check if you have:
- `amr_combined.tsv` (combined AMRFinder results)
- `vibrant_combined.tsv` (combined VIBRANT prophage results)

### Step 2: Run all analyses

If the files exist, submit the analysis job:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_kansas_2021-2025_analyses.sh
```

This will run all 6 analysis scripts and save results to your data directory.

## Expected Outputs

After the analysis completes, you'll find these files in your data directory:

### CSV Files (raw data)
- `amr_enrichment_analysis.csv` - Gene enrichment statistics
- `highly_enriched_amr_occurrences.csv` - Individual occurrences of enriched genes
- `dfra51_investigation.csv` - dfrA51 deep dive (if present in data)
- `mdsa_mdsb_investigation.csv` - mdsA+mdsB co-occurrence analysis
- `kansas_amr_prophage_contigs_DEEP_DIVE.csv` - Detailed contig-level analysis
- `amr_mobile_element_analysis.csv` - Mobile element associations

### HTML Report
- `kansas_comprehensive_amr_analysis.html` - Interactive report with plots and tables

### Log Files
All logs saved to: `analysis_results/*.log`

## What If Files Are Missing?

If `prepare_analysis_data.sh` reports missing `amr_combined.tsv` or `vibrant_combined.tsv`, you have a few options:

### Option 1: Check if pipeline already created them
```bash
cd /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod
ls -lh *_combined.tsv
```

### Option 2: Create them from individual results

The pipeline generated individual result files in subdirectories:
- AMRFinder results: `amrfinder/*_amr.tsv`
- VIBRANT results: `vibrant/*_vibrant/`

You'll need to combine these into single TSV files. Let me know if you need a script to do this!

## Checking Job Status

```bash
# Check if job is running
squeue -u tylerdoe | grep kansas_amr

# View output in real-time
tail -f kansas_analysis_*.out

# Check for errors
tail -f kansas_analysis_*.err
```

## Expected Findings (from Kansas E. coli pilot data)

Based on similar Kansas E. coli analyses, you might see:

- **~10% of AMR genes** on prophage-containing contigs
- **dfrA51** (trimethoprim): High enrichment on prophage contigs (80%+)
- **Fosfomycin resistance genes**: 30%+ enrichment
- **mdsA + mdsB**: Frequent co-occurrence on same prophage contig
- **Ground Beef**: May show highest AMR-prophage associations
- **Temporal trends**: Year-to-year variation

## Manual Analysis (Run Scripts Individually)

If you prefer to run scripts one at a time:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
DATA="/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod"

# 1. Start with enrichment analysis (fastest, most informative)
python3 bin/analyze_enriched_amr_genes.py $DATA

# 2. Deep dive into contigs
python3 bin/dig_amr_prophage_contigs.py $DATA

# 3. Investigate specific genes
python3 bin/investigate_dfra51.py $DATA
python3 bin/investigate_mdsa_mdsb.py $DATA

# 4. Generate comprehensive HTML report
python3 bin/comprehensive_amr_analysis.py $DATA

# 5. Mobile elements analysis
python3 bin/analyze_amr_mobile_elements.py $DATA
```

## Viewing Results

### On the cluster:
```bash
cd /fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod
head -20 amr_enrichment_analysis.csv
```

### Download to your local machine:
```bash
# From your local computer:
scp tylerdoe@icr-helios:"/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/*.csv" .
scp tylerdoe@icr-helios:"/fastscratch/tylerdoe/kansas_2021-2025_all_narms_v1.2mod/*.html" .

# Then open HTML report in browser
```

## Comparing v1.2-stable vs v1.2-mod

You mentioned running analyses on both branches. To do this:

### For v1.2-stable:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
git checkout v1.2-stable
sbatch run_kansas_2021-2025_analyses.sh
```

### For v1.2-mod:
```bash
git checkout v1.2-mod
sbatch run_kansas_2021-2025_analyses.sh
```

The outputs will be created in the same directory but you can rename them to compare:
```bash
mv amr_enrichment_analysis.csv amr_enrichment_v1.2-stable.csv
# Run again with v1.2-mod
# Then compare the two CSV files
```

## Available Analysis Scripts

Full list of 50+ scripts in `bin/`:

### Core analyses (recommended):
- `analyze_enriched_amr_genes.py` - **START HERE**
- `dig_amr_prophage_contigs.py`
- `comprehensive_amr_analysis.py`
- `analyze_amr_mobile_elements.py`

### Specialized investigations:
- `investigate_dfra51.py` - Trimethoprim resistance
- `investigate_mdsa_mdsb.py` - Multidrug efflux pumps
- `analyze_phage_diversity.py` - Prophage diversity
- `analyze_mlst_strain_patterns.py` - Strain typing patterns
- `analyze_temporal_source_stratification.py` - Time and source trends

### Publication-ready outputs:
- `generate_compass_summary.py` - Overall summary
- `generate_publication_figures.py` - Figures for papers
- `generate_executive_summary_dashboard.py` - Dashboard

## Troubleshooting

### "Module not found" errors
```bash
module load Python/3.9
# or
module load Anaconda3
```

### "File not found" errors
Make sure you're in the COMPASS-pipeline directory:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
ls bin/  # Should show all analysis scripts
```

### Permission denied
```bash
chmod +x bin/*.py
chmod +x *.sh
```

### Python package errors
If pandas or other packages are missing:
```bash
pip install --user pandas matplotlib seaborn scipy
```

## Getting Help

- **Analysis documentation**: `analysis/QUICK_START.md`
- **Detailed overview**: `analysis/ANALYSIS_OVERVIEW.md`
- **Enrichment details**: `analysis/ENRICHMENT_ANALYSIS_INSTRUCTIONS.md`
- **Script comments**: Each Python script has detailed docstrings

## Next Steps After Analysis

1. Review enrichment CSV to identify top genes
2. Check HTML report for visualizations
3. Investigate highly enriched genes (>30%)
4. Compare with other species/years
5. Prepare findings for publication

## Contact

For questions about the pipeline or analysis:
- Check inline documentation in scripts
- Review analysis/*.md files
- Consult COMPASS pipeline README.md

---

**Data**: Kansas 2021-2025 NARMS v1.2mod
**Pipeline**: COMPASS v1.2
**Created**: December 2024
