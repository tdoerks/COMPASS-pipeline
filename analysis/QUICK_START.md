# Quick Start: AMR-Phage Analysis

## On Beocat (SSH Connection)

### Setup
```bash
# Connect to Beocat
ssh tylerdoe@beocat.cis.ksu.edu

# Navigate to COMPASS pipeline directory
cd /bulk/tylerdoe/compass_pipeline

# Set Kansas results path
export KANSAS=/bulk/tylerdoe/kansas_results
```

## Individual Analyses (run these one at a time)

### 1. Gene Enrichment Analysis (⭐ BEST STARTING POINT)
**What it does**: Shows which AMR genes have highest % on prophage contigs

```bash
python3 bin/analyze_enriched_amr_genes.py $KANSAS
```

**Key output to look for**:
- Top genes with >30% on prophage contigs (dfrA51, glpT_E448K, fosA7)
- Drug class enrichment (FOSFOMYCIN at 32.1%)
- Creates: `amr_enrichment_analysis.csv` and `highly_enriched_amr_occurrences.csv`

**Run time**: ~10 seconds

---

### 1a. Investigate dfrA51 (trimethoprim resistance) 🔬
**What it does**: Deep dive into why dfrA51 shows 83.3% enrichment on prophage contigs

```bash
python3 bin/investigate_dfra51.py $KANSAS
```

**Key output to look for**:
- All 12 dfrA51 occurrences with prophage status
- Prophage type/quality for each occurrence
- Year and food source patterns
- Creates: `dfra51_investigation.csv`

**Run this after**: Enrichment analysis to understand the most enriched gene

---

### 1b. Investigate mdsA+mdsB Co-occurrence 🧬
**What it does**: Analyzes why mdsA and mdsB co-occur 18 times on same prophage contig

```bash
python3 bin/investigate_mdsa_mdsb.py $KANSAS
```

**Key output to look for**:
- Distance between mdsA and mdsB (operon structure?)
- Other AMR genes on same prophage contigs
- Food source and temporal patterns
- Creates: `mdsa_mdsb_investigation.csv`

**Run this after**: Deep dive analysis to explore gene pair co-occurrence

---

### 2. Deep Dive into AMR-Prophage Contigs
**What it does**: Detailed analysis of the 9.66% of AMR genes on prophage-containing contigs

```bash
python3 bin/dig_amr_prophage_contigs.py $KANSAS
```

**Key output to look for**:
- Specific AMR genes on prophage contigs with enrichment %
- Gene pairs that co-occur on same prophage contig (mdsA+mdsB appears 18 times)
- Breakdown by organism, food source (Ground Beef highest at 13.4%), year (2021 peak at 17.7%)
- Creates: `kansas_amr_prophage_contigs_DEEP_DIVE.csv`

---

### 3. Comprehensive Analysis (HTML Report)
**What it does**: Combines all analyses into interactive HTML report

```bash
python3 bin/comprehensive_amr_analysis.py $KANSAS
```

**Key output to look for**:
- Physical co-location statistics
- Mobile element associations (once MOB-suite is working)
- Sample-level patterns
- Interactive plots and charts
- Creates: `kansas_comprehensive_amr_analysis.html`

**To view on your computer**:
```bash
# On your local machine:
scp tylerdoe@beocat.cis.ksu.edu:/bulk/tylerdoe/kansas_results/kansas_comprehensive_amr_analysis.html .
# Then open in browser
```

---

### 4. Mobile Elements Analysis
**What it does**: Analyzes AMR associations with plasmids, integrases, transposases

```bash
python3 bin/analyze_amr_mobile_elements.py $KANSAS
```

**Key output to look for**:
- AMR genes on plasmids (when MOB-suite results are available)
- AMR near integrases (<5kb = likely part of integron)
- AMR near transposases (<20kb = likely mobile)
- Creates: `amr_mobile_element_analysis.csv`

---

## Run All Analyses at Once

```bash
bash analysis/RUN_ALL_ANALYSES.sh
```

This will run all 4 analyses sequentially and save logs to `${KANSAS}/analysis_results/`

---

## Check E. coli 2024 Run Status

```bash
# Check if the big E. coli run with MOB-suite fix is still running
squeue -u tylerdoe | grep ecoli

# If complete, run analyses on 2024 data:
export ECOLI_2024=/bulk/tylerdoe/ecoli_2024_results
python3 bin/analyze_enriched_amr_genes.py $ECOLI_2024
```

---

## Expected Findings from Kansas Data

### Top Enriched Genes (>30% on prophage contigs):
1. **dfrA51** (trimethoprim): 83.3% enrichment (10/12 occurrences)
2. **glpT_E448K** (fosfomycin): 34.6% enrichment (151/436)
3. **fosA7** (fosfomycin): ~31.5% enrichment

### Drug Classes:
- **FOSFOMYCIN**: 32.1% on prophage contigs (162/505 genes)
- **TRIMETHOPRIM**: ~73% (driven by dfrA51)

### Gene Pairs on Same Prophage Contig:
- **mdsA + mdsB**: 18 co-occurrences (multidrug efflux pumps)

### Food Source Patterns:
- **Ground Beef**: 13.4% AMR on prophage contigs (highest)
- **Ground Turkey**: Also elevated

### Temporal Trends:
- **2021**: 17.7% AMR on prophage contigs (peak year)
- **2025**: 7.6% (recent decrease)

---

## Next Steps After Running Analyses

1. **Review enrichment results**: Look at `amr_enrichment_analysis.csv` in Excel/Python
2. **Investigate dfrA51**: Why is it 83% on prophage contigs? Always same prophage type?
3. **Explore mdsA+mdsB**: Why do they co-occur so frequently? Composite transposon?
4. **Check Ground Beef signal**: What's special about Ground Beef samples?
5. **Compare with 2024 E. coli data**: Larger sample size (3779 samples) for validation

---

## Troubleshooting

### Scripts not found
Make sure you're in the COMPASS pipeline directory:
```bash
cd /bulk/tylerdoe/compass_pipeline
ls bin/analyze*.py  # Should show all analysis scripts
```

### Permission denied
Make scripts executable:
```bash
chmod +x bin/*.py
chmod +x analysis/RUN_ALL_ANALYSES.sh
```

### Python module errors
Load required modules on Beocat:
```bash
module load Python/3.9  # or whatever Python version has pandas
```

---

## Quick Analysis Workflow

```bash
# 1. SSH to Beocat
ssh tylerdoe@beocat.cis.ksu.edu

# 2. Navigate to pipeline
cd /bulk/tylerdoe/compass_pipeline

# 3. Run enrichment analysis (FASTEST, MOST INFORMATIVE)
python3 bin/analyze_enriched_amr_genes.py /bulk/tylerdoe/kansas_results

# 4. Review output in terminal, then check CSV files:
cd /bulk/tylerdoe/kansas_results
head -20 amr_enrichment_analysis.csv
head -20 highly_enriched_amr_occurrences.csv

# 5. Run deep dive for more details
cd /bulk/tylerdoe/compass_pipeline
python3 bin/dig_amr_prophage_contigs.py /bulk/tylerdoe/kansas_results

# 6. Download results to your computer for analysis
# (On your local machine:)
scp tylerdoe@beocat.cis.ksu.edu:/bulk/tylerdoe/kansas_results/*.csv .
```

That's it! Start with the enrichment analysis - it's the fastest and gives you the most actionable insights right away.
