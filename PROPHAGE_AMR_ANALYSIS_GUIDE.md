# Prophage AMR Analysis - Complete Guide

## Quick Start: Do Prophages Carry AMR Genes?

**TL;DR**: Use this command to get a definitive answer:
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Test on one sample first (takes 1-2 minutes)
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113
```

This runs AMRFinderPlus directly on prophage DNA sequences and tells you exactly which (if any) AMR genes are present.

---

## Background: The Problem

You have COMPASS pipeline results with:
- **AMRFinderPlus**: Detected AMR genes in whole bacterial genomes
- **VIBRANT**: Identified prophage regions in those genomes

**Question**: Do any of those AMR genes exist within prophage DNA?

**Why this matters**:
- Prophages are mobile genetic elements
- If AMR genes are in prophages, they can spread between bacteria via phage infection
- Important for understanding resistance transmission

---

## Three Analysis Methods

We developed three complementary approaches to answer this question:

### Method 1: Coordinate Matching (Fast) ⚡
**Script**: `bin/analyze_true_amr_prophage_colocation.py`

**How it works**:
1. Parse AMR gene coordinates from AMRFinderPlus (contig, start, end)
2. Parse prophage coordinates from VIBRANT (contig, start, end)
3. Check if AMR gene coordinates fall inside prophage boundaries

**Pros**:
- Very fast (seconds for hundreds of samples)
- Uses existing results, no re-computation

**Cons**:
- Requires exact coordinate matching
- May have edge cases with contig names

**Use when**: You need quick results across many samples

---

### Method 2: Annotation Search (Troubleshooting) 🔍
**Scripts**:
- `bin/search_amr_in_vibrant_annotations.py` - Search for specific AMR gene names
- `bin/search_amr_keywords_in_vibrant.py` - Search for general AMR keywords

**How it works**:
1. Get AMR gene names from AMRFinderPlus (e.g., "tetA", "blaCTX-M")
2. Search VIBRANT annotation files for those gene names
3. If found → gene is in prophage

**Result**: Typically finds 0 matches

**Why**: VIBRANT uses viral annotation databases (VOG, KEGG) not AMR-specific gene names
- Example: VIBRANT calls a gene "VOG04672 transferase" not "tetA"

**Use when**: Troubleshooting why Method 1 returned 0

---

### Method 3: Direct AMRFinder Scan (Definitive) ⭐ **RECOMMENDED**
**Script**: `bin/run_amrfinder_on_prophages.py`

**How it works**:
1. Extract prophage DNA sequences from VIBRANT output (`*_phages.fna`)
2. Run AMRFinderPlus directly on those prophage sequences
3. Report which AMR genes were detected

**Pros**:
- Most direct and definitive approach
- Uses AMR-specific tool on phage-specific sequences
- No coordinate matching issues
- No annotation format dependencies
- Clear biological answer

**Cons**:
- Slow (~1-2 minutes per sample)
- Requires re-running AMRFinderPlus

**Use when**: You want a definitive answer with high confidence

---

## Usage Examples

### Quick Test (1 sample, 1-2 minutes)
```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

# Method 3: Direct scan (recommended)
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod \
    SRR13928113
```

**Expected output**:
```
================================================================================
ANALYZING SAMPLE: SRR13928113
================================================================================

  📊 Whole-genome AMRFinder: 4 AMR genes detected

  🦠 VIBRANT identified 8 prophage regions

  🔍 Running AMRFinderPlus on prophage sequences...

  ✅ AMRFinder on prophage DNA: 1 AMR genes detected

  🎯 AMR GENES FOUND IN PROPHAGES:
     • tet(A) (TETRACYCLINE) - BLAST

  📊 COMPARISON:
     Whole genome: 4 AMR genes
     Prophage DNA: 1 AMR genes
     Prophage carries 25.0% of total AMR genes
```

---

### Fast Analysis (All samples, seconds)
```bash
# Method 1: Coordinate-based (fast)
./bin/analyze_true_amr_prophage_colocation.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod

# Generates:
# - ~/true_amr_prophage_colocation.csv
# - ~/true_amr_prophage_colocation.html (interactive report)
```

---

### Comprehensive Analysis (All samples, hours)
```bash
# Method 3: Direct scan on all samples
# WARNING: Takes ~1-2 min per sample!
./bin/run_amrfinder_on_prophages.py \
    /bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod

# Generates:
# - ~/prophage_amr_direct_scan.csv
```

---

## Interpreting Results

### ✅ Scenario 1: AMR genes found in prophages
```
AMRFinder on prophage DNA: 5 AMR genes detected
```

**Meaning**:
- Prophages DO carry AMR genes in this dataset
- These genes are potentially mobile
- Prophage-mediated resistance transfer is possible

**Next steps**:
- Identify which AMR genes are in prophages
- Analyze temporal trends (increasing over time?)
- Examine geographic patterns
- Consider drug classes affected

---

### ❌ Scenario 2: No AMR genes in prophages
```
AMRFinder on prophage DNA: 0 AMR genes detected
```

**Meaning**:
- AMR genes are NOT carried by prophages
- Resistance genes are likely chromosomal or on plasmids
- Prophage-mediated transfer not a major concern for this dataset

**Biological implications**:
- Still a valuable finding!
- Indicates resistance spread via other mechanisms
- May reflect host species, geographic region, or sampling bias

---

### ⚠️ Scenario 3: Methods disagree
```
Method 1 (Coordinate): 0 AMR genes
Method 3 (Direct scan): 5 AMR genes
```

**Meaning**: Technical issue with coordinate matching

**Action**: **Trust Method 3** - it's the most direct and definitive

**Causes**:
- Contig naming differences
- Coordinate system issues
- Edge cases in boundary detection

---

## Output Files

### Method 3 (Direct Scan)
**File**: `~/prophage_amr_direct_scan.csv`

**Columns**:
- `sample`: Sample ID
- `gene`: AMR gene name found in prophage
- `class`: Drug resistance class
- `subclass`: Drug subclass
- `method`: Detection method (BLAST/HMM)
- `prophage_contig`: Prophage sequence ID
- `whole_genome_amr_count`: Total AMR genes in genome
- `prophage_count`: Number of prophages identified

**Use for**: Detailed gene-level analysis

---

### Method 1 (Coordinate-Based)
**Files**:
- `~/true_amr_prophage_colocation.csv` - Detailed results
- `~/true_amr_prophage_colocation.html` - Interactive report

**Columns**:
- `sample`, `organism`, `year`
- `amr_gene`, `amr_class`, `contig`
- `amr_start`, `amr_end`
- `prophage_id`, `prophage_start`, `prophage_end`
- `distance` (0 = inside prophage)
- `category` (within_prophage / outside_prophage)

**Use for**: Quick overview, visual exploration

---

## Recommended Workflow

### For First-Time Users:
1. **Test on 1 sample** with Method 3 (1-2 min)
   ```bash
   ./bin/run_amrfinder_on_prophages.py results/ SRR13928113
   ```

2. **Interpret result**:
   - If AMR genes found → Run Method 3 on more samples
   - If 0 AMR genes → Confirmed, prophages don't carry resistance

3. **Scale up** based on findings:
   - Method 1 for quick overview (all samples in seconds)
   - Method 3 for high-confidence subset (selected samples)

---

### For Large Datasets (1000+ samples):
1. **Quick scan** with Method 1 (seconds)
   ```bash
   ./bin/analyze_true_amr_prophage_colocation.py results/
   ```

2. **Validate** with Method 3 on subset (10-20 samples)
   ```bash
   for sample in SRR001 SRR002 SRR003; do
       ./bin/run_amrfinder_on_prophages.py results/ $sample
   done
   ```

3. **Compare** Method 1 vs Method 3 results:
   - If both return ~0 → High confidence negative
   - If Method 3 finds AMR genes → Use Method 3 for all samples

---

### For Publication-Quality Analysis:
1. **Run Method 3 on all samples** (or representative subset)
   - Most defensible in peer review
   - Clear methods section: "AMRFinderPlus v3.x run on prophage sequences"

2. **Export results** to CSV

3. **Generate figures**:
   - Proportion of AMR genes in prophages vs chromosomal
   - Temporal trends (if applicable)
   - Geographic patterns (if applicable)
   - Drug class distribution in prophages

---

## Technical Details

### What does VIBRANT output?

VIBRANT creates `{sample}_phages.fna` with prophage sequences:
```
>NODE_4_length_123456_cov_12.34_fragment_1 # 10000 # 35000 # 1 # ...
ATCGATCGATCG...
>NODE_5_length_98765_cov_8.76_fragment_1 # 5000 # 25000 # 1 # ...
GCTAGCTAGCTA...
```

Each sequence is a prophage region identified in the assembly.

### What does AMRFinderPlus do?

AMRFinderPlus scans nucleotide sequences for:
- Known AMR genes (BLAST against curated database)
- AMR protein domains (HMM searches)
- Point mutations conferring resistance

When we run it on prophage sequences, we get AMR genes specifically in phage DNA.

---

## Troubleshooting

### "AMRFinder not found"
**Problem**: `amrfinder` command not in PATH

**Solution**: Load AMRFinder module or install
```bash
# On Beocat
module load AMRFinder

# Or check installation
which amrfinder
```

---

### "No prophage sequences found"
**Problem**: VIBRANT output missing

**Solution**: Check VIBRANT ran successfully
```bash
ls results/vibrant/SRR*_phages.fna
```

If files missing, VIBRANT may have failed or found no prophages.

---

### "Method 3 very slow"
**Problem**: Takes hours for large datasets

**Solution**:
- Test on subset first (5-10 samples)
- Use Method 1 for quick overview
- Run Method 3 on representative samples only
- Consider parallelization (future feature)

---

## Summary

**Goal**: Determine if prophages carry AMR genes

**Recommended approach**: Method 3 (Direct AMRFinder scan)
- Most definitive
- Clear biological interpretation
- Worth the computational cost

**Quick alternative**: Method 1 (Coordinate matching)
- Fast for large datasets
- Good for initial exploration
- Validate with Method 3 if critical

**Result interpretation**:
- AMR genes found → Prophages carry resistance
- 0 AMR genes → Chromosomal/plasmid resistance
- Both are valuable scientific findings!

---

## Questions?

See detailed documentation: `AMR_IN_VIBRANT_SEARCH.md`

Or examine the scripts:
- `bin/run_amrfinder_on_prophages.py` - Direct scan (recommended)
- `bin/analyze_true_amr_prophage_colocation.py` - Coordinate matching
- `bin/search_amr_keywords_in_vibrant.py` - Keyword search

**Created**: January 2026
**Last Updated**: January 2026
