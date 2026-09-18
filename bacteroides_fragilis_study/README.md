# Bacteroides fragilis Prophage Study - Oxygen Gradient Analysis

## Overview
Analysis of **Bacteroides fragilis** (obligate anaerobe) prophage burden to test the **oxygen-dependent prophage burden hypothesis**.

## Why Bacteroides fragilis?
- **Obligate anaerobe** (like Fusobacterium)
- **Most abundant gut bacteria** (~30% of gut microbiome)
- **Same niche as E. coli** but different oxygen requirement
- **Perfect comparison**: Same environment, different metabolism
- **Well-studied**: ~1000+ genomes available

## Hypothesis
**Bacteroides (anaerobe) should have LOW prophage burden (~1-2/genome) like Fusobacterium, NOT high like E. coli (8.2/genome)**

## Oxygen Gradient Study Context

| Organism | Metabolism | Niche | Prophages/Genome | Status |
|----------|------------|-------|------------------|--------|
| **Bacteroides** | **Obligate anaerobe** | **Gut** | **? (THIS STUDY)** | **Running** |
| Fusobacterium | Obligate anaerobe | Oral/Gut | 1.3 | ✓ Complete |
| E. coli | Facultative | Gut | 8.2 | Literature |
| Salmonella | Facultative | Gut/Food | 4.2 | ✓ Complete |

## Expected Results
- **Prophage burden**: 1-2 prophages/genome (LOW)
- **Similar to Fusobacterium** (also anaerobe)
- **Much lower than E. coli** (same niche, facultative)
- **Validates hypothesis**: Oxygen requirement determines prophage burden

## Usage

### Step 1: Download accessions
```bash
cd bacteroides_fragilis_study/
python3 scripts/fetch_bacteroides.py
```

### Step 2: Generate samplesheet
```bash
python3 scripts/create_samplesheet.py
```

### Step 3: Submit to Beocat
```bash
sbatch run_bacteroides.sh
```

## Analysis Pipeline
1. **COMPASS**: Assembly, QC, MLST, AMRFinder, VIBRANT, MOB-suite
2. **Prophage extraction**: Count integrated prophages per genome
3. **Comparison**: Compare to Fusobacterium and E. coli
4. **Statistical test**: Anaerobes vs Facultative prophage burden

## Expected Files
```
bacteroides_results/
├── vibrant/          # Prophage identification
├── amrfinder/        # Resistance/virulence genes
├── mlst/             # Strain typing
├── mobsuite/         # Plasmids
├── busco/            # Assembly quality
└── summary/          # Integrated results
```

## Analysis Questions
1. **Prophage burden**: How many prophages per Bacteroides genome?
2. **Comparison to Fusobacterium**: Same low burden in both anaerobes?
3. **Comparison to E. coli**: Gut niche but different oxygen → different prophage load?
4. **Oxygen hypothesis**: Do both anaerobes have low burden despite different phylogeny?

## Publication Angle
**"Oxygen requirement, not phylogeny or niche, determines prophage burden: Evidence from Bacteroides and Fusobacterium"**

---
*Part of Oxygen Gradient Prophage Study*
*Organism #2: Bacteroides fragilis (obligate anaerobe)*
