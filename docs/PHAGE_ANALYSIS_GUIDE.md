# Enhanced Prophage Analysis Guide

## Overview

COMPASS pipeline now includes **3 different approaches** for prophage/viral analysis:

| Method | Input | Purpose | Speed | Accuracy |
|--------|-------|---------|-------|----------|
| **VIBRANT** | Assembly | Quick prophage prediction | Fast | Good |
| **PhiSpy/PHASTER** | Assembly | Better prophage boundaries | Medium | Better |
| **viralFlye** | Raw reads | Complete viral genomes | Slow | Best |

## Quick Start

### Use Default (VIBRANT only)
```bash
nextflow run main.nf --input samples.csv
```

### Add PhiSpy for better predictions
```bash
nextflow run main.nf --input samples.csv --run_phaster
```

### Add viralFlye for complete genomes
```bash
nextflow run main.nf --input samples.csv --run_viralflye
```

### Use all three methods
```bash
nextflow run main.nf --input samples.csv --run_phaster --run_viralflye
```

## Module Details

### 1. VIBRANT (Default)

**Container:** `staphb/vibrant`
**Input:** Assembled contigs (SPAdes output)
**Output:**
- `vibrant/` - Full VIBRANT results
- `${sample}_phages.fna` - Predicted prophage sequences

**Pros:**
- Fast (~5-10 min per sample)
- Good for initial screening
- Identifies prophage-like genes

**Cons:**
- Boundaries may be inaccurate
- Higher false positive rate
- Doesn't distinguish functional vs remnant prophages

**Use when:** Quick analysis, many samples

---

### 2. PhiSpy/PHASTER

**Container:** `quay.io/biocontainers/phispy:4.2.21`
**Input:** Assembled contigs
**Output:**
- `phaster/${sample}_phaster/prophage_coordinates.tsv` - Precise coordinates
- `phaster/${sample}_phaster/prophage.fasta` - Prophage sequences
- `phaster/${sample}_phaster/bacteria.fasta` - Non-prophage regions

**Pros:**
- More accurate boundaries
- Lower false positive rate
- Better at distinguishing prophages from genomic islands

**Cons:**
- Slower than VIBRANT (~15-20 min per sample)
- May miss highly divergent prophages

**Use when:** Need accurate boundaries for downstream analysis

**Output format (prophage_coordinates.tsv):**
```
Contig	Start	End	Length	Num_CDS	Category
NODE_1	145000	167000	22000	28	Active
NODE_3	89000	105000	16000	19	Questionable
```

---

### 3. viralFlye + viralVerify

**Containers:**
- `staphb/flye:2.9.3` (viralFlye)
- `quay.io/biocontainers/viralverify:1.1` (viralVerify)

**Input:** Raw sequencing reads (FASTQ)
**Output:**
- `viralflye/${sample}_viralflye/assembly.fasta` - Viral genome assemblies
- `viralverify/${sample}_viralverify/*_result_table.csv` - Contig classifications
- `viral_contigs/${sample}_viral_contigs.fasta` - Filtered viral sequences only

**Pros:**
- Assembles complete, circular viral genomes
- Can find free phages (not just prophages)
- High quality viral sequences

**Cons:**
- Very slow (~1-2 hours per sample)
- Resource intensive (16 CPUs, 32GB RAM)
- May not work well with low viral abundance

**Use when:**
- Need complete phage genomes
- Looking for actively replicating phages
- Publishing phage sequences

**Output format (result_table.csv):**
```
Contig name,Length,Prediction,Score
contig_1,45231,Virus,0.98
contig_2,3456,Plasmid,0.87
contig_3,152341,Chromosome,0.23
```

---

## Comparison Workflow

To validate prophage predictions across all three methods:

```bash
# Run all three
nextflow run main.nf \\
  --input samples.csv \\
  --run_phaster \\
  --run_viralflye \\
  --outdir results_all_methods
```

Then compare results:
```bash
# Compare VIBRANT vs PhiSpy
python3 bin/compare_prophage_predictions.py \\
  --vibrant results_all_methods/vibrant/ \\
  --phispy results_all_methods/phaster/ \\
  --output comparison_report.html
```

---

## Resource Requirements

### VIBRANT
```
CPUs: 8
Memory: 16 GB
Time: 12 hours (max)
```

### PhiSpy/PHASTER
```
CPUs: 4
Memory: 8 GB
Time: 6 hours (max)
```

### viralFlye
```
CPUs: 16
Memory: 32 GB
Time: 8 hours (max)
```

---

## For Kansas E. coli AMR Analysis

### Current Setup (VIBRANT only)
- Fast screening of 788 samples
- Identified prophage regions
- Found 0% AMR genes within prophages

### Recommended Next Steps

**Option 1: Validate with PhiSpy** (Recommended)
```bash
nextflow run main.nf \\
  --input kansas_samples.csv \\
  --run_phaster \\
  --max_cpus 16
```
- Re-analyzes with better prophage boundaries
- Confirms 0% co-location finding
- Takes ~1-2 days for 788 samples

**Option 2: Assemble complete viral genomes** (If supervisor wants phage sequences)
```bash
# Run on subset first (e.g., 10 samples)
nextflow run main.nf \\
  --input kansas_subset.csv \\
  --run_viralflye \\
  --max_cpus 32
```
- Gets actual phage genome sequences
- Can annotate phage genes
- Takes ~20 hours for 10 samples

---

## Troubleshooting

### PhiSpy fails with "No prophages found"
- Normal if sample has no prophages
- Check `phispy.log` for details

### viralFlye produces no contigs
- May need more sequencing depth
- Check if reads are truly viral (most should be bacterial)

### Out of memory errors
- Reduce `--max_memory 32.GB` in config
- Use fewer parallel samples

---

## Integration with Existing Analysis

Current Kansas analysis used VIBRANT results. To re-analyze with PhiSpy:

```bash
# 1. Run PhiSpy on all samples
nextflow run main.nf --input kansas_ALL.csv --run_phaster

# 2. Re-run AMR-prophage co-location analysis with PhiSpy results
python3 bin/analyze_true_amr_prophage_colocation.py \\
  --results-dir results/phaster/ \\
  --amr-dir results/amrfinderplus/ \\
  --output kansas_phispy_colocation.csv
```

---

## Questions?

**Which method should I use?**
- Publishing? → viralFlye (complete genomes)
- Validation? → PhiSpy (accurate boundaries)
- Screening? → VIBRANT (fast)

**Do I need all three?**
- No! VIBRANT alone is fine for most analyses
- Add PhiSpy if reviewers question prophage calls
- Add viralFlye only if you need actual phage sequences

**How long will this take?**
- VIBRANT: ~10 min/sample
- PhiSpy: ~20 min/sample
- viralFlye: ~2 hours/sample

For 788 Kansas samples:
- VIBRANT: ~5.5 days (already done!)
- PhiSpy: ~11 days
- viralFlye: ~66 days (run subset!)

---

**Last updated:** 2025-11-13
**Pipeline version:** v1.2-dev
