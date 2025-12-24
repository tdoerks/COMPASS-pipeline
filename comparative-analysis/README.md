# COMPASS Comparative Analysis Pipeline

Analysis pipeline for integrating plasmid, prophage, and AMR data across multiple years of E. coli COMPASS results.

## Overview

This pipeline reveals novel connections between:
- **Plasmids** (MOBsuite data) - replicon types, mobility
- **Prophages** (VIBRANT data) - integrated phages, gene cargo
- **Antimicrobial Resistance** (AMRFinder data) - resistance genes and mechanisms
- **Sequence Types** (MLST data) - clonal context

**Research Questions:**
1. Which plasmid types carry the most AMR genes?
2. Do prophages co-occur with specific plasmid families?
3. How do mobile element patterns change over time (2022-2024)?
4. Can we identify "super-spreader" plasmids?

## Directory Structure

```
comparative-analysis/
├── scripts/           # Analysis scripts
├── data/             # Extracted CSV files
├── results/          # Analysis outputs
├── figures/          # Visualization outputs
└── README.md         # This file
```

## Installation

### Required Python Packages

```bash
# On Beocat, load Python module
module load Python/3.9

# Create virtual environment
python -m venv compass_analysis_env
source compass_analysis_env/bin/activate

# Install requirements
pip install pandas numpy matplotlib seaborn networkx scipy
```

## Usage

### Step 1: Extract Data from COMPASS Results

Run the parsing scripts on each year's data:

```bash
cd /homes/tylerdoe/beocat-astronomy/comparative-analysis

# Parse 2022 data
python scripts/parse_amrfinder.py \
    -i /bulk/tylerdoe/archives/kansas_2022_ecoli/amrfinder \
    -o data/amr_2022.csv \
    -y 2022

python scripts/parse_mobsuite.py \
    -i /bulk/tylerdoe/archives/kansas_2022_ecoli/mobsuite \
    -o data/plasmid_2022.csv \
    -y 2022

python scripts/parse_vibrant.py \
    -i /bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant \
    -o data/prophage_2022.csv \
    -y 2022

python scripts/parse_mlst.py \
    -i /bulk/tylerdoe/archives/kansas_2022_ecoli/mlst/mlst_results.tsv \
    -o data/mlst_2022.csv \
    -y 2022

# Repeat for 2023
python scripts/parse_amrfinder.py \
    -i /bulk/tylerdoe/archives/results_ecoli_2023/amrfinder \
    -o data/amr_2023.csv \
    -y 2023

python scripts/parse_mobsuite.py \
    -i /bulk/tylerdoe/archives/results_ecoli_2023/mobsuite \
    -o data/plasmid_2023.csv \
    -y 2023

python scripts/parse_vibrant.py \
    -i /bulk/tylerdoe/archives/results_ecoli_2023/vibrant \
    -o data/prophage_2023.csv \
    -y 2023

python scripts/parse_mlst.py \
    -i /bulk/tylerdoe/archives/results_ecoli_2023/mlst/mlst_results.tsv \
    -o data/mlst_2023.csv \
    -y 2023

# Repeat for 2024
python scripts/parse_amrfinder.py \
    -i /bulk/tylerdoe/archives/results_ecoli_all_2024/amrfinder \
    -o data/amr_2024.csv \
    -y 2024

python scripts/parse_mobsuite.py \
    -i /bulk/tylerdoe/archives/results_ecoli_all_2024/mobsuite \
    -o data/plasmid_2024.csv \
    -y 2024

python scripts/parse_vibrant.py \
    -i /bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant \
    -o data/prophage_2024.csv \
    -y 2024

python scripts/parse_mlst.py \
    -i /bulk/tylerdoe/archives/results_ecoli_all_2024/mlst/mlst_results.tsv \
    -o data/mlst_2024.csv \
    -y 2024
```

### Step 2: Integrate All Data

Combine all years into integrated dataset:

```bash
python scripts/integrate_data.py \
    --amr data/amr_2022.csv data/amr_2023.csv data/amr_2024.csv \
    --plasmids data/plasmid_2022.csv data/plasmid_2023.csv data/plasmid_2024.csv \
    --prophages data/prophage_2022.csv data/prophage_2023.csv data/prophage_2024.csv \
    --mlst data/mlst_2022.csv data/mlst_2023.csv data/mlst_2024.csv \
    --output results/integrated_summary.csv
```

This creates:
- `results/integrated_summary.csv` - Per-sample summary
- `results/integrated_summary_cooccurrence.csv` - Plasmid-AMR associations

### Step 3: Run Analyses

(Analysis scripts to be added next)

```bash
# Association analysis
python scripts/analyze_associations.py -i results/integrated_summary.csv

# Network analysis
python scripts/analyze_networks.py -i results/integrated_summary.csv

# Temporal trends
python scripts/analyze_trends.py -i results/integrated_summary.csv
```

### Step 4: Generate Visualizations

(Visualization scripts to be added next)

```bash
# Network plots
python scripts/plot_networks.py -i results/integrated_summary.csv

# Heatmaps
python scripts/plot_heatmaps.py -i results/integrated_summary.csv

# Trend plots
python scripts/plot_trends.py -i results/integrated_summary.csv
```

## Output Files

### Data Files

- `data/amr_YEAR.csv` - AMR genes per sample
- `data/plasmid_YEAR.csv` - Plasmid replicons per sample
- `data/prophage_YEAR.csv` - Prophage predictions per sample
- `data/mlst_YEAR.csv` - Sequence types per sample

### Results Files

- `results/integrated_summary.csv` - Master dataset linking all elements
- `results/integrated_summary_cooccurrence.csv` - Plasmid-AMR co-occurrence matrix
- `results/associations.csv` - Statistical associations
- `results/network_metrics.csv` - Network analysis results
- `results/temporal_trends.csv` - Year-over-year changes

### Figures

- `figures/plasmid_amr_network.png` - Network graph
- `figures/cooccurrence_heatmap.png` - Heatmap of associations
- `figures/temporal_trends.png` - Trends over time
- `figures/sankey_diagram.png` - Flow of resistance genes

## Data Schemas

### integrated_summary.csv

| Column | Description |
|--------|-------------|
| sample_id | Sample identifier (SRR accession) |
| year | Year of sample collection |
| sequence_type | MLST sequence type |
| num_amr_genes | Number of AMR genes detected |
| amr_classes | AMR drug classes (comma-separated) |
| amr_genes | Specific AMR genes (comma-separated) |
| num_plasmids | Number of plasmids detected |
| replicon_types | Plasmid replicon types (comma-separated) |
| plasmid_mobility | Predicted mobility (conjugative, mobilizable, non-mobilizable) |
| num_prophages | Number of prophages detected |
| prophage_scaffolds | Scaffolds containing prophages |

## Research Questions & Analyses

### 1. Plasmid-AMR Associations

**Question:** Which plasmid replicon types are most associated with multidrug resistance?

**Analysis:**
- Chi-square tests for replicon type vs AMR class
- Calculate odds ratios
- Identify "high-risk" plasmid types

### 2. Mobile Element Networks

**Question:** How do plasmids, prophages, and AMR genes cluster together?

**Analysis:**
- Build co-occurrence networks
- Community detection algorithms
- Identify central "hub" elements

### 3. Temporal Dynamics

**Question:** Are certain plasmid-AMR combinations increasing over time?

**Analysis:**
- Linear regression on prevalence 2022→2024
- Emerging vs declining combinations
- Forecast future trends

### 4. Super-Spreader Plasmids

**Question:** Can we identify plasmids carrying unusually high AMR gene cargo?

**Analysis:**
- Rank plasmids by AMR gene count
- Characterize their replicon types
- Track their prevalence

## Publication Potential

This analysis is **genuinely novel** because:

1. **Multi-element integration** - Most studies analyze plasmids OR prophages OR AMR, not all together
2. **Temporal dynamics** - Tracking changes across 3 years
3. **Large scale** - Thousands of E. coli genomes
4. **Public health relevance** - Identifies high-risk mobile elements

**Potential venues:**
- *mSystems* or *mBio* - Microbiology-focused
- *Microbiome* - If you find interesting patterns
- *BMC Genomics* - Methods + results

## Next Steps

1. ✅ Data extraction scripts created
2. ✅ Integration script created
3. 🔄 Analysis scripts (in progress)
4. 🔄 Visualization scripts (in progress)
5. ⏳ Run on full dataset
6. ⏳ Generate publication figures
7. ⏳ Write manuscript

## Contact

Tyler Doerksen - tdoerks@vet.k-state.edu

## References

- COMPASS Pipeline: [GitHub repo]
- MOBsuite: Robertson & Nash (2018)
- VIBRANT: Kieft et al. (2020)
- AMRFinderPlus: Feldgarden et al. (2019)
- MLST: Jolley & Maiden (2010)
