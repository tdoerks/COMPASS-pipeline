# AMR-in-Prophage Results Validation Guide

## Overview

This guide helps you verify that AMR genes detected in prophages (Method 3 results) are real and not false positives. Use these validation tools before publication or making biological conclusions.

## Quick Start

```bash
# 1. Statistical check (5 minutes)
./bin/validate_amr_prophage_statistics.py /path/to/method3_results.csv

# 2. Spot check samples (30 minutes)
./bin/spot_check_amr_prophages.py /bulk/path/results SRR12345678 SRR12345679 SRR12345680

# 3. Visualize gene context (15 minutes)
./bin/visualize_amr_prophage_context.py /bulk/path/results SRR12345678
```

---

## Validation Tools

### Tool 1: Statistical Consistency Checks ⚡ FAST

**Script**: `bin/validate_amr_prophage_statistics.py`

**Purpose**: Quick statistical validation without re-scanning data

**What it checks**:
- ✅ Proportion of AMR in prophages vs whole genome (expect 1-10%)
- ✅ Gene types (mobile vs chromosomal)
- ✅ Sample distribution (many samples with few genes each)
- ✅ Drug class diversity

**Usage**:
```bash
# Single dataset
./bin/validate_amr_prophage_statistics.py method3_direct_scan.csv

# Multiple years
./bin/validate_amr_prophage_statistics.py \
    ecoli_2021/method3_direct_scan.csv \
    ecoli_2022/method3_direct_scan.csv \
    ecoli_2023/method3_direct_scan.csv \
    ecoli_2024/method3_direct_scan.csv

# Save report
./bin/validate_amr_prophage_statistics.py results.csv --output validation_report.txt
```

**Output Interpretation**:
- **PASS** ✅ - Results look statistically reasonable, safe to proceed
- **WARNING** ⚠️ - Minor concerns, consider spot-checking
- **SUSPICIOUS** 🚨 - Serious concerns, manual validation required

**Red Flags**:
- >30% of AMR genes in prophages (unusual)
- Chromosomal genes (gyrA, parC, rpoB) in prophages (suspicious)
- One sample with 50+ genes (likely artifact)
- Only one drug class found (contamination?)

---

### Tool 2: Spot Check Validation 🔍 DETAILED

**Script**: `bin/spot_check_amr_prophages.py`

**Purpose**: Deep-dive validation on selected samples

**What it does**:
- Extracts prophage sequences
- Shows AMR gene positions and characteristics
- Checks sequence quality (GC content, gaps)
- Generates FASTA for BLAST validation

**Usage**:
```bash
# Check specific samples
./bin/spot_check_amr_prophages.py /bulk/path/results SRR12345678 SRR12345679

# Generate BLAST file
./bin/spot_check_amr_prophages.py /bulk/path/results SRR12345678 \
    --blast-output for_blast.fasta

# Save detailed report
./bin/spot_check_amr_prophages.py /bulk/path/results SRR12345678 \
    --report spot_check_report.txt
```

**BLAST Validation Steps**:
1. Run spot check script with `--blast-output prophages.fasta`
2. Go to https://blast.ncbi.nlm.nih.gov/Blast.cgi
3. Choose "Nucleotide BLAST" (blastn)
4. Upload `prophages.fasta`
5. Select database: "Nucleotide collection (nr/nt)"
6. Run BLAST
7. Check results:
   - ✅ **PASS**: Top hits are phage/prophage sequences
   - ⚠️ **WARNING**: Mixed hits (some phage, some bacterial)
   - 🚨 **FAIL**: Top hits are bacterial chromosomal DNA

**What to Look For**:
- Prophage length: 10-80 kb (typical), <5 kb (fragment/cryptic), >80 kb (jumbo)
- GC content: Should differ from host (~35-55% typical)
- Assembly gaps: <1% N bases (good quality)

---

### Tool 3: Gene Context Visualization 📊 VISUAL

**Script**: `bin/visualize_amr_prophage_context.py`

**Purpose**: Create gene maps showing AMR positions in prophages

**What it shows**:
- Prophage length
- AMR gene positions
- Gene orientation (+ or - strand)
- Drug classes

**Usage**:
```bash
# Visualize single sample
./bin/visualize_amr_prophage_context.py /bulk/path/results SRR12345678

# Multiple samples
./bin/visualize_amr_prophage_context.py /bulk/path/results \
    SRR12345678 SRR12345679 SRR12345680

# Save to file
./bin/visualize_amr_prophage_context.py /bulk/path/results SRR12345678 \
    --output gene_maps.txt
```

**Example Output**:
```
========================================
Prophage: SRR12345678_fragment_3
Length: 42,531 bp
AMR genes: 2
========================================

Scale:
0                                                           42,531 bp
[----------------------------------------------------------------------]

AMR Genes:
      >>>>>  tetA (Tetracycline) | 12,450-13,650 bp (+)
                  <<<<<  aph (Aminoglycoside) | 28,100-28,900 bp (-)
```

**Interpretation**:
- `>>>>>` = Gene on forward strand (+)
- `<<<<<` = Gene on reverse strand (-)
- Position shows where in prophage the AMR gene is located

---

## Validation Workflow

### Step 1: Quick Statistical Check (5 min)

Run statistical validation on all datasets:

```bash
./bin/validate_amr_prophage_statistics.py \
    ecoli_2021/method3_direct_scan.csv \
    ecoli_2022/method3_direct_scan.csv \
    ecoli_2023/method3_direct_scan.csv \
    ecoli_2024/method3_direct_scan.csv \
    --output statistical_validation.txt
```

**Decision**:
- ✅ **All checks PASS** → Proceed to publication (optional: spot check 2-3 samples)
- ⚠️ **Some WARNINGS** → Proceed to Step 2 (spot check flagged samples)
- 🚨 **SUSPICIOUS flags** → Proceed to Step 2 immediately

### Step 2: Spot Check Samples (30 min - 2 hrs)

Select samples for validation:
- 5-10 random samples with AMR in prophages
- All samples flagged as suspicious in Step 1
- Samples with unusual gene counts or types

```bash
# Create list of samples to check
SAMPLES="SRR12345678 SRR12345679 SRR12345680 SRR12345681 SRR12345682"

# Run spot check
./bin/spot_check_amr_prophages.py /bulk/path/results $SAMPLES \
    --blast-output for_blast.fasta \
    --report spot_check_results.txt
```

**Then**:
1. BLAST the exported sequences (see BLAST Validation Steps above)
2. Verify top hits are phage/prophage sequences
3. Check for red flags (bacterial chromosomal hits)

**Decision**:
- ✅ **BLAST confirms phages** → Proceed to Step 3 or publication
- ⚠️ **Mixed BLAST results** → Investigate specific samples
- 🚨 **BLAST shows bacterial DNA** → Major issue, re-evaluate pipeline

### Step 3: Visualize Gene Context (15 min)

For 2-3 confirmed samples, visualize gene organization:

```bash
./bin/visualize_amr_prophage_context.py /bulk/path/results \
    SRR12345678 SRR12345679 SRR12345680 \
    --output gene_context_maps.txt
```

**Check**:
- AMR genes are within prophage boundaries
- Gene positions match AMRFinder coordinates
- Multiple genes in same prophage cluster together

---

## Expected Results (Normal vs Suspicious)

### ✅ Expected (Results are Real)

**Statistical**:
- 1-10% of AMR genes in prophages
- Mostly mobile genes: tet, aph, sul, bla, cat, erm
- Many samples, 1-5 genes each
- 5-10 drug classes represented

**BLAST**:
- Top hits: "prophage", "phage", "bacteriophage"
- E-values: < 1e-50 (strong match)
- Coverage: >70%

**Visual**:
- AMR genes clearly within prophage regions
- Gene sizes reasonable (500-3000 bp)
- Prophage sizes: 10-80 kb

### 🚨 Suspicious (Potential False Positives)

**Statistical**:
- >30% of AMR genes in prophages
- Chromosomal genes: gyrA, parC, rpoB, folP
- One sample with 50+ genes
- Only 1-2 drug classes

**BLAST**:
- Top hits: "chromosome", "genomic DNA", no phage mention
- Poor coverage (<50%)
- No phage-related hits in top 10

**Visual**:
- AMR genes at prophage boundaries (edge artifacts)
- Prophage regions <5 kb (fragments)
- High % of Ns (assembly gaps)

---

## Common Issues and Solutions

### Issue 1: High Proportion of AMR in Prophages (>30%)

**Possible causes**:
- Highly mobile population (real but unusual)
- VIBRANT over-predicting prophages
- Contaminated sequencing data

**Solution**:
1. Check VIBRANT quality scores
2. Spot check 10 samples with BLAST
3. Compare to literature (typical: 1-10%)

### Issue 2: Chromosomal AMR Genes in Prophages

**Possible causes**:
- False positive prophage predictions
- Prophage inserted near chromosomal AMR locus
- Misannotation

**Solution**:
1. BLAST those specific sequences
2. Check if genes are at prophage boundaries
3. Review VIBRANT prediction scores

### Issue 3: One Sample with Many Genes

**Possible causes**:
- Real hypervirulent strain with AMR-rich prophages
- Assembly artifact (contamination)
- VIBRANT mis-classified large region as prophage

**Solution**:
1. Spot check that specific sample
2. BLAST prophage sequences
3. Check assembly quality metrics
4. Consider excluding as outlier if suspicious

---

## For Publication

Include these validation results:

### Main Text
- "We validated AMR-prophage findings using statistical consistency checks (see Methods)"
- "BLAST analysis confirmed prophage sequences (Supplementary Table X)"
- Report proportion of AMR in prophages with confidence

### Methods Section
```
AMR-prophage validation: We verified results using three approaches:
(1) Statistical consistency checks: proportion of AMR in prophages,
gene type distribution, and sample distribution;
(2) BLAST validation: representative prophage sequences were queried
against NCBI nr/nt database to confirm phage identity;
(3) Gene context visualization: AMR gene positions were mapped within
prophage boundaries to verify co-location.
```

### Supplementary Data
- Table: Statistical validation summary (Tool 1 output)
- Table: BLAST results for spot-checked samples (Tool 2)
- Figure: Example gene maps (Tool 3)
- Table: Complete list of AMR genes in prophages

---

## Interpretation Guidelines

### How much validation is needed?

**For preliminary analysis**:
- Run Tool 1 (statistical checks)
- If PASS → sufficient

**For publication**:
- Run Tool 1 (statistical checks)
- Run Tool 2 on 5-10 samples (spot check + BLAST)
- Run Tool 3 on 2-3 samples (visualization)
- Document all results in supplementary data

**If major funding/high-impact paper**:
- All of the above
- Plus: Manual curation of all suspicious samples
- Plus: Literature comparison of gene lists
- Plus: Experimental validation (PCR, sequencing)

---

## Troubleshooting

**Q: Tool says "CSV not found"**
A: Check file path. Method 3 CSV is usually `method3_direct_scan.csv` in the analysis output directory.

**Q: BLAST shows no phage hits**
A: This is a red flag. The prophage prediction may be wrong. Investigate with Tool 3 (visualization).

**Q: Statistical check shows SUSPICIOUS**
A: Don't panic! Run Tool 2 (spot check) on flagged samples. Often it's just a few outliers.

**Q: What if all checks PASS but results seem too good?**
A: This is normal! Prophages DO carry AMR genes. If validation passes, trust your results.

**Q: Should I exclude suspicious samples?**
A: Yes, for publication. Document why (failed BLAST, assembly artifact, etc.).

---

## Contact & Support

If you have questions about validation:
1. Check this guide first
2. Review Tool 1 output interpretation
3. Run Tool 2 for detailed diagnostics
4. Contact: Tyler Doerks, Kansas State University

---

## Version Info

- **Guide Version**: 1.0
- **Date**: January 2026
- **Pipeline**: COMPASS v1.3
- **Tools**: validate_amr_prophage_statistics.py, spot_check_amr_prophages.py, visualize_amr_prophage_context.py
