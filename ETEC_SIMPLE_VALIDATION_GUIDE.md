# ETEC Validation - Simplified Comparison Guide

## Overview

This guide explains how to generate **simple validation comparisons** between your COMPASS pipeline results and the published ETEC reference genome paper (Figure S12, S13, and Table S4).

**No dendrograms or clustering** - just straightforward gene detection validation.

---

## What You'll Get

Four simple outputs:

1. **`amr_gene_comparison.csv`** - Table showing which genes COMPASS detected vs. paper
2. **`amr_gene_counts.png`** - Bar chart of AMR gene counts per strain
3. **`prophage_count_comparison.png`** - COMPASS vs. paper prophage counts
4. **`figure_s12_style_heatmap.png`** - Simple presence/absence heatmap (purple=present, white=absent)
5. **`validation_summary_statistics.csv`** - Summary table

---

## Quick Start (On Beocat)

After your COMPASS validation run completes:

```bash
cd /homes/tylerdoe/COMPASS-pipeline

# Run comparison script
./data/validation/compare_etec_simple.sh
```

That's it! Results will be in `figures/etec_validation/`

---

## What Gets Compared

### Figure S12 - AMR Genes
The script compares COMPASS AMRFinder results against ~60 AMR genes reported in the paper:
- **Acquired resistance genes**: aph(3")-Ib, aph(6")-Id, blaTEM, etc.
- **Efflux pumps**: acrAB, emrAB, mdtABCEFGHMNOP, etc.
- **Regulators**: marA, gadW, cpxA, etc.

### Figure S13 - Efflux & Porins
Compares detection of:
- Efflux systems (acrAB-tolC, emrAB, mdtABC, etc.)
- Porins (ompC, glpT)

### Table S4 - Prophages
Compares prophage counts:
- **Expected** (from paper): E925=5, E1649=4, E36=13, E2980=7, E1441=4, E1779=9, E562=2, E1373=3
- **COMPASS** (VIBRANT detections)

---

## Output Descriptions

### 1. AMR Gene Comparison Table (`amr_gene_comparison.csv`)

Gene-by-gene comparison showing:
- Each detected gene
- Presence in each strain (Yes/No)
- Whether gene appears in paper Figure S12 (Yes/No)

**Use this to**: Verify specific gene detections

### 2. AMR Gene Counts (`amr_gene_counts.png`)

Bar chart showing how many AMR genes COMPASS detected in each strain.

**Use this to**: Quick overview of detection counts

### 3. Prophage Comparison (`prophage_count_comparison.png`)

Side-by-side bars comparing:
- Paper's reported prophage counts (Table S4)
- COMPASS VIBRANT detections

**Use this to**: Validate prophage detection accuracy

### 4. Simple Heatmap (`figure_s12_style_heatmap.png`)

Presence/absence matrix (like Figure S12):
- Rows = ETEC strains
- Columns = AMR genes detected
- Purple = present, White = absent
- **NO DENDROGRAM** - just the heatmap

**Use this to**: Visual validation of detection patterns

### 5. Summary Statistics (`validation_summary_statistics.csv`)

Per-sample summary:
- AMR gene count
- Prophage count (COMPASS)
- Prophage count (expected from paper)
- Difference

**Use this to**: Overall validation metrics

---

## Manual Usage (If You Want More Control)

```bash
# Generate comparisons
./bin/compare_etec_validation_simple.py \
    data/validation/etec_results \
    --output figures/etec_validation

# View summary
cat figures/etec_validation/validation_summary_statistics.csv

# Transfer to local machine
scp -r tylerdoe@beocat.ksu.edu:/homes/tylerdoe/COMPASS-pipeline/figures/etec_validation ./
```

---

## Expected vs. Actual Comparison

### AMR Gene Detection
Your COMPASS results should detect similar AMR gene profiles to the paper. Check:
- **Figure S12 genes**: Did COMPASS find the main acquired resistance genes?
- **Efflux systems**: Most strains should have complete efflux operons

### Prophage Detection
Prophage counts may vary slightly due to:
- Different prediction tools (paper used multiple tools, COMPASS uses VIBRANT)
- Threshold differences
- **Tolerance**: ±2 prophages is acceptable

---

## Interpreting Results

### Good Validation
- **AMR genes**: 80-100% of paper-reported genes detected
- **Prophage counts**: Within ±2 of expected counts
- **Gene patterns**: Similar across strains (e.g., efflux pumps present in all)

### Investigate If:
- **AMR genes missing**: Check if paper genes are truly "acquired" (scope=core)
- **Prophage differences >3**: Check assembly quality (BUSCO scores)
- **Systematic issues**: Check if specific genes missing across all samples

---

## Comparison with Paper

### To validate visually:

1. **Open paper's Figure S12** (page 13 of supplemental PDF)
   - Located at: `data/validation/41598_2021_88316_MOESM1_ESM.pdf`
   - Your `figure_s12_style_heatmap.png` should look similar

2. **Compare gene lists**
   - Open `amr_gene_comparison.csv`
   - Check which paper genes are in "In Paper S12" = Yes
   - Verify COMPASS detected those same genes

3. **Check prophage counts**
   - Paper Table S4 (page 22-27): Shows prophage locations
   - Your `prophage_count_comparison.png`: Shows if counts match

---

## Next Steps After Validation

### If Results Look Good:
1. Include figures in Paper 1 supplemental materials
2. Add validation metrics to Methods section
3. Tag COMPASS v1.3 release

### If Discrepancies Found:
1. Check specific genes manually in AMRFinder output
2. Verify prophage predictions in VIBRANT output
3. Consult ground truth CSV for expected values

---

## Troubleshooting

### "Results directory not found"
```bash
# Check if results exist
ls data/validation/etec_results/amrfinder/

# If not, transfer from Beocat
scp -r tylerdoe@beocat.ksu.edu:/homes/tylerdoe/COMPASS-pipeline/data/validation/etec_results \
    data/validation/
```

### "No AMRFinder results found"
Check your COMPASS run completed successfully:
```bash
ls data/validation/etec_results/amrfinder/*_amr.tsv
# Should show 8 files (one per sample)
```

### Gene name mismatches
Some genes may have different names:
- Paper: `aph(3")-Ib` vs. COMPASS: `APH(3')-Ib`
- Script does flexible matching, but check CSV if concerned

---

## Files Created

**New scripts:**
- `bin/compare_etec_validation_simple.py` - Main comparison script
- `data/validation/compare_etec_simple.sh` - Helper script

**Removes:**
- The complex dendrogram script is still available if needed
- Use simple version for validation, complex for publication figures (if desired)

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine

---

**Generated**: February 12, 2026
**Purpose**: Simple validation comparison (no dendrograms)
**Status**: Ready to use with Beocat ETEC results
