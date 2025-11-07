# COMPASS Analysis Tools - Quick Reference

This document provides a quick overview of all analysis and reporting tools available in the COMPASS pipeline.

---

## 🎯 What Do You Want to Do?

### Generate a Pipeline Execution Report
**"I want a comprehensive HTML report showing what the pipeline did at each step"**

```bash
python3 bin/generate_pipeline_report.py /path/to/results
```

**Output**: Beautiful HTML report with statistics from all 11 pipeline steps
**Documentation**: `docs/PIPELINE_REPORT.md`

---

### Analyze AMR-Prophage Associations
**"I want to see which AMR genes are enriched on prophage contigs"**

#### Quick Analysis (10 seconds)
```bash
python3 bin/analyze_enriched_amr_genes.py /path/to/results
```
**Output**: Gene enrichment statistics, top enriched genes
**Files**: `amr_enrichment_analysis.csv`, `highly_enriched_amr_occurrences.csv`

#### Deep Dive (30 seconds)
```bash
# Auto-detect Kansas results and run all analyses
./quick_dig_kansas.sh

# OR manually specify path
bash analysis/RUN_ALL_ANALYSES.sh /path/to/results
```
**Output**: 4+ analysis scripts, comprehensive CSV files
**Documentation**: `analysis/ANALYSIS_OVERVIEW.md`, `analysis/QUICK_START.md`

---

### Investigate Specific Genes
**"Why is dfrA51 so highly enriched on prophage contigs?"**

```bash
python3 bin/investigate_dfra51.py /path/to/results
```
**Output**: All dfrA51 occurrences with prophage details, patterns by year/source
**File**: `dfra51_investigation.csv`

**"Why do mdsA and mdsB always co-occur?"**

```bash
python3 bin/investigate_mdsa_mdsb.py /path/to/results
```
**Output**: Gene distance analysis, operon structure detection
**File**: `mdsa_mdsb_investigation.csv`

---

### Get Detailed AMR-Prophage Breakdown
**"Show me every AMR gene on prophage contigs"**

```bash
python3 bin/dig_amr_prophage_contigs.py /path/to/results
```
**Output**: All 419 AMR genes on prophage contigs with metadata
**File**: `kansas_amr_prophage_contigs_DEEP_DIVE.csv`

---

### Analyze Mobile Elements
**"How are AMR genes associated with plasmids, integrases, transposons?"**

```bash
python3 bin/analyze_amr_mobile_elements.py /path/to/results
```
**Output**: AMR-plasmid associations, AMR near mobile elements
**File**: `amr_mobile_element_analysis.csv`

---

### Generate Comprehensive AMR Analysis
**"I want an interactive HTML report with all AMR-phage patterns"**

```bash
python3 bin/comprehensive_amr_analysis.py /path/to/results
```
**Output**: HTML dashboard with interactive plots and statistics
**File**: `kansas_comprehensive_amr_analysis.html`

---

## 📁 Tool Categories

### 🔬 Analysis Scripts

| Script | Purpose | Output | Run Time |
|--------|---------|--------|----------|
| `analyze_enriched_amr_genes.py` | Gene enrichment statistics | 2 CSV files | ~10 sec |
| `investigate_dfra51.py` | dfrA51 deep dive | 1 CSV file | ~5 sec |
| `investigate_mdsa_mdsb.py` | mdsA+mdsB analysis | 1 CSV file | ~5 sec |
| `dig_amr_prophage_contigs.py` | All AMR on prophage contigs | 1 CSV file | ~15 sec |
| `analyze_amr_mobile_elements.py` | Mobile element associations | 1 CSV file | ~20 sec |
| `comprehensive_amr_analysis.py` | Interactive HTML dashboard | 1 HTML file | ~30 sec |

### 📊 Reporting Scripts

| Script | Purpose | Output | Run Time |
|--------|---------|--------|----------|
| `generate_pipeline_report.py` | Full pipeline execution report | 1 HTML file | ~30 sec |
| `generate_summary_report.py` | High-level summary (STUB) | 1 HTML file | N/A |

### 🚀 Helper Scripts

| Script | Purpose |
|--------|---------|
| `quick_dig_kansas.sh` | Auto-detect and run all deep dive analyses |
| `analysis/RUN_ALL_ANALYSES.sh` | Run all 4 core analyses with logging |

---

## 📚 Documentation Files

| File | Content |
|------|---------|
| `analysis/ANALYSIS_OVERVIEW.md` | Complete overview of AMR-phage analysis suite |
| `analysis/QUICK_START.md` | Fast reference for running each analysis |
| `analysis/ENRICHMENT_ANALYSIS_INSTRUCTIONS.md` | Detailed enrichment analysis guide |
| `docs/PIPELINE_REPORT.md` | Pipeline execution report documentation |
| `FEATURE_IDEAS.md` | Enhancement ideas and TODO tracking |
| `SESSION_SUMMARY.md` | Summary of work completed this session |

---

## 🎓 Recommended Workflow

### For Initial Data Review

1. **Generate pipeline report** to see overall statistics
   ```bash
   python3 bin/generate_pipeline_report.py /path/to/results
   ```

2. **Run enrichment analysis** to identify interesting patterns
   ```bash
   python3 bin/analyze_enriched_amr_genes.py /path/to/results
   ```

3. **Review CSVs** to see top enriched genes
   ```bash
   head -20 amr_enrichment_analysis.csv | column -t -s,
   ```

### For Deep Investigation

4. **Run deep dive analyses** on patterns of interest
   ```bash
   ./quick_dig_kansas.sh  # Runs all 4 deep dive scripts
   ```

5. **Investigate specific genes** that show high enrichment
   ```bash
   python3 bin/investigate_dfra51.py /path/to/results
   ```

6. **Generate comprehensive report** for publication/sharing
   ```bash
   python3 bin/comprehensive_amr_analysis.py /path/to/results
   ```

---

## 💡 Tips

### Multi-Year Analysis
All scripts automatically detect year directories and combine data:
```
results/
├── 2021/
│   ├── amr_combined.tsv
│   └── vibrant_combined.tsv
├── 2022/
├── 2023/
└── ...
```

Just point to the parent directory!

### Parallel Execution
Run multiple analyses simultaneously on different datasets:
```bash
# Terminal 1
python3 bin/generate_pipeline_report.py /path/to/2024_results &

# Terminal 2
python3 bin/analyze_enriched_amr_genes.py /path/to/2024_results &
```

### Output Organization
All scripts save output files to the same directory as input results, making them easy to find:
```
results/
├── amr_combined.tsv
├── vibrant_combined.tsv
├── pipeline_execution_report.html  ← Generated
├── amr_enrichment_analysis.csv     ← Generated
└── dfra51_investigation.csv        ← Generated
```

### Quick Viewing
```bash
# View CSV in terminal
head -20 file.csv | column -t -s,

# Copy to local machine for Excel
scp user@server:/path/to/*.csv .
```

---

## 🐛 Troubleshooting

### "Script not found"
```bash
# Make sure you're in the pipeline directory
cd /path/to/compass-pipeline

# Check script exists
ls bin/analyze_enriched_amr_genes.py
```

### "Results directory not found"
```bash
# Check path is correct
ls /path/to/results

# For multi-year, check year directories exist
ls /path/to/results/202*
```

### "No data in output"
```bash
# Check combined files exist
ls /path/to/results/amr_combined.tsv
ls /path/to/results/vibrant_combined.tsv

# Check files aren't empty
wc -l /path/to/results/*.tsv
```

### "Permission denied"
```bash
# Make scripts executable
chmod +x bin/*.py
chmod +x *.sh
```

---

## 📞 Getting Help

1. **Check documentation**:
   - `analysis/QUICK_START.md` - Fast reference
   - `analysis/ANALYSIS_OVERVIEW.md` - Complete overview
   - `docs/PIPELINE_REPORT.md` - Report generator guide

2. **Check inline help**:
   ```bash
   python3 bin/analyze_enriched_amr_genes.py --help
   ```

3. **Review examples** in documentation files

4. **Check `FEATURE_IDEAS.md`** for planned enhancements

---

## 🔄 Staying Up to Date

```bash
# Pull latest analysis scripts
git pull origin v1.2-dev

# Check what's new
git log --oneline -10

# See changed files
git diff --name-only HEAD~5
```

---

## 🎯 Next Steps

After running analyses, consider:

1. **Validate findings** on larger datasets (E. coli 2024 national data)
2. **Investigate mechanisms** behind enriched genes (prophage integration sites?)
3. **Compare organisms** (Salmonella vs E. coli patterns?)
4. **Publish results** using HTML reports as supplementary materials

---

**Last Updated**: 2025-11-07
**Branch**: v1.2-dev
**Total Scripts**: 8 analysis + 2 reporting + 2 helpers = 12 tools ready to use
