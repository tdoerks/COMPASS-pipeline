# Tree Sample Metadata - Usage Guide

## Purpose

When viewing the Fusobacterium prophage tree, you'll see labels like:
```
SRR10901569_NODE_9_length_118569_cov_128.637039_fragment_3
_R_SRR848065_NODE_6_length_128875_cov_180.419461_fragment_2
```

These scripts create **lookup tables** so you can easily identify:
- Which **subspecies** each sample belongs to
- What **host** it came from
- Where it was **isolated** from
- **How many prophages** each sample has

---

## Two Output Files

### 1. Comprehensive Metadata Table (Supplementary Material)

**File**: `tree_sample_metadata_supplementary.tsv`

**Purpose**: Full metadata table for publication as supplementary material

**Columns**:
- Sample_ID (SRR accession)
- Subspecies (F. nucleatum, F. necrophorum, etc.)
- Host (Homo sapiens, Bos taurus, etc.)
- Isolation_Source (raw text from NCBI)
- Isolation_Source_Category (Oral, GI, Blood, Clinical, Other)
- Geographic_Location
- Country
- Collection_Date
- BioProject
- BioSample
- Study_Title
- Prophage_Count (from VIBRANT analysis)
- Assembly_Size_Mb
- Library_Strategy
- Platform
- Center_Name

**Format**: Tab-separated values (TSV), can open in Excel/Google Sheets

**Use for**:
- Supplementary Table in manuscript
- Statistical analyses
- Detailed sample information

### 2. Quick Reference Guide (For Viewing Tree)

**File**: `tree_quick_reference.txt`

**Purpose**: Simple lookup table to use while viewing tree in iTOL

**Format**:
```
SRR10901569     | F. nucleatum             | Human          | Oral
SRR848065       | F. nucleatum             | Human          | GI
SRR11789049     | F. nucleatum             | Human          | Blood
SRR37881923     | F. necrophorum           | Bovine         | GI
```

**Use for**:
- Quick lookups: "What subspecies is SRR10901569?"
- Identifying patterns while viewing tree
- Easy reference without opening spreadsheet

---

## How to Generate These Files

### On Beocat:

```bash
ssh tylerdoe@beocat.cis.ksu.edu

cd /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/scripts

# Run the script
bash run_create_tree_metadata.sh
```

This will:
1. Parse the prophage tree to extract all sample IDs
2. Match each sample to its metadata
3. Create both output files
4. Print summary statistics

### Download to Local Machine:

```bash
# Full metadata table
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/tree_sample_metadata_supplementary.tsv .

# Quick reference
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/fusobacterium_necrophorum_study/data/tree_quick_reference.txt .
```

---

## Example Usage Workflows

### Workflow 1: Viewing Tree in iTOL

1. Upload `prophage_tree.nwk` to iTOL
2. Open `tree_quick_reference.txt` in a text editor
3. When you see a tip labeled `SRR10901569_NODE_9_...`:
   - Look up `SRR10901569` in quick reference
   - See it's *F. nucleatum* from human oral cavity
4. Identify patterns:
   - Do all *F. necrophorum* cluster together?
   - Do bovine samples cluster separately from human?

### Workflow 2: Creating Publication Figure

1. Upload tree to iTOL
2. Use `tree_sample_metadata_supplementary.tsv` to create custom annotations:
   - Color by Subspecies
   - Add outer ring for Host
   - Add outer ring for Isolation_Source_Category
3. Export high-resolution figure
4. Include `tree_sample_metadata_supplementary.tsv` as Supplementary Table 1

### Workflow 3: Statistical Analysis

```R
# Load metadata
metadata <- read.table("tree_sample_metadata_supplementary.tsv",
                       header=TRUE, sep="\t")

# Test: Do F. necrophorum samples have more prophages?
necrophorum <- subset(metadata, grepl("necrophorum", Subspecies))
mean(necrophorum$Prophage_Count)

# Compare oral vs GI
oral <- subset(metadata, Isolation_Source_Category == "Oral")
gi <- subset(metadata, Isolation_Source_Category == "Gastrointestinal")
t.test(oral$Prophage_Count, gi$Prophage_Count)
```

---

## Understanding Tree Labels

### Label Format

Tree labels contain multiple pieces of information:

```
SRR10901569_NODE_9_length_118569_cov_128.637039_fragment_3
│           │      │            │               │
│           │      │            │               └─ Prophage number in this sample
│           │      │            └─────────────────── Sequencing coverage
│           │      └──────────────────────────────── Contig length (bp)
│           └─────────────────────────────────────── Contig number
└─────────────────────────────────────────────────── Sample accession (SRR)
```

### Special Prefixes

- **`_R_`**: Indicates reverse complement sequence (MAFFT auto-reversed for alignment)
  - Example: `_R_SRR848065_...` is the same sample as `SRR848065` but reverse strand

### Multiple Prophages per Sample

Some samples appear multiple times because they have multiple prophages:
```
SRR10901569_NODE_1_..._fragment_5   ← 5th prophage
SRR10901569_NODE_2_..._fragment_1   ← 1st prophage
SRR10901569_NODE_9_..._fragment_3   ← 3rd prophage
```

All three are from sample `SRR10901569`, but different prophage elements.

---

## Interpretation Questions

Use the metadata files to answer:

### 1. Subspecies Clustering?

**Question**: Do prophages from the same Fusobacterium subspecies cluster together?

**How to check**:
1. Look at tree in iTOL with subspecies colors
2. Reference quick reference guide
3. If YES → Vertical inheritance (prophages co-evolved with host)
4. If NO → Horizontal transfer (prophages moving between species)

**Expected**: YES (based on low prophage burden hypothesis)

### 2. F. necrophorum Unique?

**Question**: Do *F. necrophorum* prophages form a distinct clade?

**How to check**:
1. Find all *F. necrophorum* samples in quick reference
2. See if they cluster together in tree
3. If YES → Species-specific prophages
4. If NO → Shared with other Fusobacterium

**Importance**: *F. necrophorum* is the professor's target organism

### 3. Host Specificity?

**Question**: Do bovine isolate prophages differ from human isolates?

**How to check**:
1. Color tree by Host (from metadata table)
2. Look for host-based clustering
3. If YES → Host-specific prophage ecology
4. If NO → Prophages don't depend on host species

### 4. Niche Adaptation?

**Question**: Do oral prophages differ from GI prophages?

**How to check**:
1. Use Isolation_Source_Category from metadata
2. Look for oral vs GI clustering patterns
3. If YES → Niche-specific prophage adaptation
4. If NO → Prophages similar across body sites

---

## Files Created by Scripts

### Input Files (Required)

| File | Location | Description |
|------|----------|-------------|
| `prophage_tree.nwk` | `fusobacterium_results/analysis/phylogenomics/` | Newick tree file |
| `fusobacterium_metadata.tsv` | `fusobacterium_necrophorum_study/data/` | NCBI metadata |
| `fusobacterium_metadata_prophage_merged.tsv` | `fusobacterium_necrophorum_study/data/` | Metadata + prophage counts |

### Output Files (Generated)

| File | Description | Use |
|------|-------------|-----|
| `tree_sample_metadata_supplementary.tsv` | Full metadata table | Publication, detailed analysis |
| `tree_quick_reference.txt` | Simple lookup table | Quick reference while viewing tree |

---

## Troubleshooting

### "Sample not found in metadata"

Some samples in tree might not have metadata if:
- Metadata download had errors
- Sample was removed from NCBI
- SRR accession extraction failed

**Solution**: Check if sample exists in `fusobacterium_metadata.tsv`

### "Wrong subspecies shown"

NCBI organism field can be inconsistent:
- Some say "Fusobacterium nucleatum"
- Some say "Fusobacterium nucleatum subsp. nucleatum"
- Some use old taxonomy

**Solution**: Manual curation may be needed for publication

### "Prophage counts don't match"

Tree shows 28 sequences but only ~15-20 unique samples because:
- Some samples have multiple prophages
- Each prophage is a separate tip in tree
- Prophage_Count column shows total per sample

---

## Citation & Documentation

Include these files in your manuscript supplementary materials:

**Supplementary Table S1**: Tree Sample Metadata
- File: `tree_sample_metadata_supplementary.tsv`
- Description: "Metadata for Fusobacterium samples included in prophage phylogenetic analysis, including subspecies, host, isolation source, and prophage counts."

**Supplementary File S1**: Prophage Phylogenetic Tree
- File: `prophage_tree.nwk`
- Description: "Maximum-likelihood phylogenetic tree of 28 Fusobacterium prophage sequences built using MAFFT alignment and FastTree (GTR model)."

---

## Quick Command Reference

```bash
# Generate metadata files on Beocat
bash run_create_tree_metadata.sh

# Download to local
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/.../tree_sample_metadata_supplementary.tsv .
scp tylerdoe@beocat.cis.ksu.edu:/fastscratch/.../tree_quick_reference.txt .

# View quick reference
less tree_quick_reference.txt

# Open metadata table
open tree_sample_metadata_supplementary.tsv  # Mac
xdg-open tree_sample_metadata_supplementary.tsv  # Linux

# Count samples by subspecies
cut -f2 tree_sample_metadata_supplementary.tsv | sort | uniq -c
```

---

*Fusobacterium Prophage Phylogenomic Analysis*
*Tree metadata tools for sample identification and interpretation*
