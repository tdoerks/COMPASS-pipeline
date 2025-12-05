# Kansas 2021-2025 Analysis - Quick Start Guide

## Your Setup

- **Pipeline**: `/fastscratch/tylerdoe/COMPASS-pipeline/`
- **Data**: `/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod/`

The pipeline and data can be in different locations - this is totally fine!

## Step-by-Step Instructions

### Step 1: Check Data Structure

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
bash check_kansas_data.sh
```

**What this does**: Checks if your data has the combined TSV files needed for analysis.

---

### Step 2: Create Combined Files (if needed)

If Step 1 shows missing files, run:

```bash
bash create_combined_files.sh
```

**What this does**:
- Combines all AMRFinder results into `amr_combined.tsv`
- Combines all VIBRANT results into `vibrant_combined.tsv`
- Takes ~5-10 minutes depending on sample count

---

### Step 3: Quick Test (Recommended)

Test one analysis to make sure everything works:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
python3 bin/analyze_enriched_amr_genes.py /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod
```

**What this does**: Runs the enrichment analysis in ~10 seconds. You'll see output in your terminal showing:
- Top AMR genes on prophage contigs
- Drug class enrichment
- Creates `amr_enrichment_analysis.csv` in your data directory

If this works, everything is configured correctly!

---

### Step 4: Run All Analyses

Submit the full analysis job:

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch run_kansas_analyses_bulk.sh
```

**What this does**: Runs all 6 analyses as a SLURM job (~30-60 minutes)

---

## Monitoring Progress

Check job status:
```bash
squeue -u tylerdoe | grep kansas_analysis
```

Watch the log in real-time:
```bash
tail -f /bulk/tylerdoe/archives/kansas_analysis_*.out
```

---

## Expected Results

After completion, you'll find these in your data directory:

```
/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod/
├── amr_combined.tsv                     ← Combined input (created in step 2)
├── vibrant_combined.tsv                 ← Combined input (created in step 2)
├── amr_enrichment_analysis.csv          ← Gene enrichment statistics
├── highly_enriched_amr_occurrences.csv  ← Detailed gene occurrences
├── kansas_amr_prophage_contigs_DEEP_DIVE.csv  ← Full analysis
├── kansas_comprehensive_amr_analysis.html     ← Interactive HTML report!
├── amr_mobile_element_analysis.csv      ← Plasmid/mobile element data
├── dfra51_investigation.csv             ← dfrA51 deep dive (if present)
├── mdsa_mdsb_investigation.csv          ← mdsA/mdsB analysis (if present)
└── analysis_results/                     ← Log files
    ├── 01_enrichment_analysis.log
    ├── 02_deep_dive.log
    ├── 03_dfra51.log
    ├── 04_mdsa_mdsb.log
    ├── 05_comprehensive.log
    └── 06_mobile_elements.log
```

---

## Key Findings to Look For

Based on similar Kansas E. coli analyses:

### Gene Enrichment
- **dfrA51** (trimethoprim): Often 80%+ on prophage contigs
- **glpT_E448K** (fosfomycin): ~35% enrichment
- **fosA7** (fosfomycin): ~30% enrichment

### Drug Classes
- **FOSFOMYCIN**: ~32% on prophage contigs
- **TRIMETHOPRIM**: High enrichment if dfrA51 present

### Co-occurrence Patterns
- **mdsA + mdsB**: Multidrug efflux pumps often on same prophage contig
- Other gene pairs that suggest mobile genetic elements

### Source Patterns
- Ground Beef may show highest AMR-prophage associations
- Temporal trends across 2021-2025

---

## Viewing Results

### On the cluster:
```bash
cd /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod

# View enrichment results
less amr_enrichment_analysis.csv

# Count highly enriched genes
awk -F'\t' '$4 > 30 {print $1, $4}' amr_enrichment_analysis.csv | head -20
```

### On your local computer:
```bash
# Download CSV files
scp "tylerdoe@icr-helios:/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod/*.csv" .

# Download HTML report
scp tylerdoe@icr-helios:/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod/kansas_comprehensive_amr_analysis.html .

# Open HTML report in browser
open kansas_comprehensive_amr_analysis.html  # Mac
# or
xdg-open kansas_comprehensive_amr_analysis.html  # Linux
```

---

## Troubleshooting

### "Module not found" errors
```bash
module load Python/3.9
# or
module load Anaconda3
```

### "amr_combined.tsv not found"
Run step 2 to create the combined files:
```bash
bash create_combined_files.sh
```

### Python package errors
```bash
pip install --user pandas matplotlib seaborn scipy
```

### Permission errors
```bash
chmod +x bin/*.py
chmod +x *.sh
```

---

## Next Steps After Analysis

1. **Review enrichment CSV** - Identify top genes (>30% on prophage)
2. **Open HTML report** - Interactive visualizations
3. **Investigate specific genes** - Use the investigation CSVs
4. **Compare organisms** - If you have Salmonella/Campylobacter data
5. **Prepare findings** - For manuscript/presentation

---

## Need Help?

- **Documentation**: Check `analysis/` directory in pipeline
- **Script details**: Each Python script has detailed comments
- **Issues**: Look at log files in `analysis_results/`

---

**Last Updated**: December 2024
**Pipeline Version**: v1.2-mod
**Dataset**: Kansas 2021-2025 NARMS
