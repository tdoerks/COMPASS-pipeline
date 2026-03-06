# Quick Start Guide - COMPASS Comparative Analysis

Get up and running in 5 minutes!

## Setup (One Time)

### 1. Copy Analysis Pipeline to Beocat

```bash
# On Beocat
cd /homes/tylerdoe
git clone https://github.com/tdoerks/beocat-astronomy.git
cd beocat-astronomy/comparative-analysis
```

### 2. Install Python Dependencies (One-Time)

```bash
# Load Python module
module load Python/3.9

# Install required packages (uses --user to install in your home directory)
pip install --user pandas numpy
```

That's it! No virtual environment needed.

## Run the Pipeline

### Option A: Automated (Recommended)

Run the master script to process all 3 years at once:

```bash
cd /homes/tylerdoe/beocat-astronomy/comparative-analysis
module load Python/3.9
bash run_pipeline.sh
```

This will:
1. Extract AMR, plasmid, prophage, and MLST data from all 3 years
2. Integrate everything by sample ID
3. Create summary statistics
4. Generate co-occurrence matrices

**Time:** ~30-60 minutes depending on dataset size

### Option B: Manual (Step by Step)

#### Step 1: Extract 2022 Data

```bash
python scripts/parse_amrfinder.py -i /bulk/tylerdoe/archives/kansas_2022_ecoli/amrfinder -o data/amr_2022.csv -y 2022
python scripts/parse_mobsuite.py -i /bulk/tylerdoe/archives/kansas_2022_ecoli/mobsuite -o data/plasmid_2022.csv -y 2022
python scripts/parse_vibrant.py -i /bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant -o data/prophage_2022.csv -y 2022
python scripts/parse_mlst.py -i /bulk/tylerdoe/archives/kansas_2022_ecoli/mlst/*.tsv -o data/mlst_2022.csv -y 2022
```

#### Step 2: Repeat for 2023 and 2024

```bash
# 2023
python scripts/parse_amrfinder.py -i /bulk/tylerdoe/archives/results_ecoli_2023/amrfinder -o data/amr_2023.csv -y 2023
python scripts/parse_mobsuite.py -i /bulk/tylerdoe/archives/results_ecoli_2023/mobsuite -o data/plasmid_2023.csv -y 2023
python scripts/parse_vibrant.py -i /bulk/tylerdoe/archives/results_ecoli_2023/vibrant -o data/prophage_2023.csv -y 2023
python scripts/parse_mlst.py -i /bulk/tylerdoe/archives/results_ecoli_2023/mlst/*.tsv -o data/mlst_2023.csv -y 2023

# 2024
python scripts/parse_amrfinder.py -i /bulk/tylerdoe/archives/results_ecoli_all_2024/amrfinder -o data/amr_2024.csv -y 2024
python scripts/parse_mobsuite.py -i /bulk/tylerdoe/archives/results_ecoli_all_2024/mobsuite -o data/plasmid_2024.csv -y 2024
python scripts/parse_vibrant.py -i /bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant -o data/prophage_2024.csv -y 2024
python scripts/parse_mlst.py -i /bulk/tylerdoe/archives/results_ecoli_all_2024/mlst/*.tsv -o data/mlst_2024.csv -y 2024
```

#### Step 3: Integrate All Data

```bash
python scripts/integrate_data.py \
    --amr data/amr_*.csv \
    --plasmids data/plasmid_*.csv \
    --prophages data/prophage_*.csv \
    --mlst data/mlst_*.csv \
    --output results/integrated_summary.csv
```

## Check Results

```bash
# View summary statistics
cat logs/integrate_data.log

# Check sample counts
wc -l results/integrated_summary.csv

# Preview data
head -20 results/integrated_summary.csv

# Check plasmid-AMR associations
head -20 results/integrated_summary_cooccurrence.csv
```

## What You Should See

After successful run, all results will be in:

```
/bulk/tylerdoe/archives/comparative_analysis_results/
├── data/
│   ├── amr_2022.csv           # ~2,800 samples × AMR genes
│   ├── amr_2023.csv           # ~3,800 samples × AMR genes
│   ├── amr_2024.csv           # ~XXXX samples × AMR genes
│   ├── plasmid_2022.csv       # Plasmid replicons
│   ├── plasmid_2023.csv
│   ├── plasmid_2024.csv
│   ├── prophage_2022.csv      # Prophage predictions
│   ├── prophage_2023.csv
│   ├── prophage_2024.csv
│   ├── mlst_2022.csv          # Sequence types
│   ├── mlst_2023.csv
│   └── mlst_2024.csv
├── results/
│   ├── integrated_summary.csv              # Main output!
│   └── integrated_summary_cooccurrence.csv # Plasmid-AMR associations
└── logs/
    └── *.log                   # Processing logs
```

## Explore Your Data

### Look at integrated summary:

```bash
# Navigate to results
cd /bulk/tylerdoe/archives/comparative_analysis_results/results

# How many samples per year?
cut -d',' -f2 integrated_summary.csv | sort | uniq -c

# Top AMR classes
cut -d',' -f6 integrated_summary.csv | head -100

# Top plasmid types
cut -d',' -f9 integrated_summary.csv | head -100
```

### Transfer to local machine:

```bash
# From your local computer
scp tylerdoe@beocat.ksu.edu:/bulk/tylerdoe/archives/comparative_analysis_results/results/*.csv ./
```

Open in Excel, R, Python, etc.!

## Next Steps

1. **Explore the data** - Look for interesting patterns
2. **Run analyses** (scripts coming soon):
   - Statistical associations
   - Network analysis
   - Temporal trends
3. **Create visualizations** (scripts coming soon):
   - Network graphs
   - Heatmaps
   - Trend plots

## Troubleshooting

**Error: "No such file or directory"**
- Check paths in `run_pipeline.sh` match your actual data locations
- Use `ls /bulk/tylerdoe/archives/` to verify directory names

**Error: "ModuleNotFoundError: No module named 'pandas'"**
- Activate virtual environment: `source compass_analysis_env/bin/activate`
- Install packages: `pip install pandas numpy matplotlib seaborn networkx scipy`

**Empty output files**
- Check logs: `cat logs/parse_*.log`
- Verify COMPASS outputs exist: `ls /bulk/tylerdoe/archives/kansas_2022_ecoli/`

**Script hangs/runs slowly**
- Large datasets take time (30-60 min is normal)
- Check progress: `tail -f logs/integrate_data.log`

## Questions?

Check the full README.md for detailed documentation.

**You're analyzing connections between plasmids, prophages, and AMR across thousands of E. coli genomes - that's genuinely novel research!** 🔬🦠
