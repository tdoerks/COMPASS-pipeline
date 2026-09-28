# Clostridium difficile Prophage Burden Study

## Overview

**Organism**: *Clostridioides difficile* (formerly *Clostridium difficile*)
**Metabolism**: Obligate anaerobe (no oxygen tolerance)
**Niche**: Human gut pathogen (C. difficile infection)
**Study Context**: Oxygen gradient prophage burden analysis

## Study Rationale

### Position in Oxygen Gradient Study

This is the **third obligate anaerobe** in our comparative analysis:

1. **Fusobacterium** (obligate anaerobe) → 1.3 prophages/genome ✓
2. **Bacteroides fragilis** (obligate anaerobe, gut) → Running...
3. **Clostridium difficile** (obligate anaerobe, gut pathogen) → This study

### Why Clostridium difficile?

1. **Obligate anaerobe**: Cannot survive in presence of oxygen
2. **Same niche as E. coli**: Human gut (perfect comparison)
3. **Clinical importance**: Major cause of hospital-acquired infections
4. **Well-studied**: Large number of sequenced genomes available
5. **Spore-forming**: Unique stress response (how does this affect prophage burden?)

### Expected Results

**Hypothesis**: LOW prophage burden (1-2 prophages/genome)

**Reasoning**:
- Obligate anaerobe (like Fusobacterium: 1.3 prophages/genome)
- Limited oxidative stress (no ROS-driven prophage selection)
- Spore formation provides alternative stress response
- Gut niche but anaerobic (vs E. coli facultative)

**Critical comparison**:
- **C. difficile** (anaerobe, gut) vs **E. coli** (facultative, gut)
- Both gut bacteria, different oxygen tolerance
- Expected: C. difficile << E. coli prophage burden
- Would strongly support oxygen-dependent prophage hypothesis

## Workflow

### Step 1: Fetch SRA Accessions

```bash
cd clostridium_difficile_study
python3 scripts/fetch_clostridium.py
```

**Output**: `data/sra_accessions_clostridium.txt`

**Search criteria**:
- Organism: *Clostridioides difficile* (or *Clostridium difficile*)
- Platform: Illumina
- Source: GENOMIC
- Strategy: WGS

### Step 2: Create Samplesheet

```bash
python3 scripts/create_samplesheet.py
```

**Output**: `data/samplesheet_clostridium.txt`

### Step 3: Launch COMPASS Pipeline

```bash
# Copy scripts to Beocat
rsync -av clostridium_difficile_study/ tylerdoe@beocat.cis.ksu.edu:/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/clostridium_difficile_study/

# SSH to Beocat
ssh tylerdoe@beocat.cis.ksu.edu

# Launch job
cd /fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/clostridium_difficile_study
sbatch run_clostridium.sh
```

### Step 4: Monitor Job

```bash
# Check job status
squeue -u tylerdoe

# View output
tail -f /fastscratch/tylerdoe/slurm-clostridium-<JOBID>.out
```

### Step 5: Analyze Results

After pipeline completes:

1. **Extract prophage counts**: Analyze VIBRANT results
2. **Compare to other anaerobes**: Fusobacterium, Bacteroides
3. **Compare to E. coli**: Same niche, different oxygen tolerance
4. **Statistical analysis**: Test oxygen gradient hypothesis

## Expected Timeline

- **SRA download**: 2-5 days (depends on sample count)
- **Assembly**: 3-7 days
- **Annotation**: 2-4 days
- **Total**: ~1-2 weeks

## Analysis Plan

### Primary Analysis: Prophage Burden

**Research Questions**:
1. What is mean prophage burden in C. difficile?
2. How does it compare to Fusobacterium (1.3) and Bacteroides?
3. How does it compare to E. coli (~8)?

**Expected Result**: 1-2 prophages/genome (similar to Fusobacterium)

### Secondary Analysis: Spore Formation

**Question**: Do spore-forming bacteria have different prophage ecology?

**Comparison**:
- C. difficile (spore-forming, anaerobe)
- Fusobacterium (non-spore, anaerobe)
- Bacillus (spore-forming, aerobe) - future study

### Tertiary Analysis: Pathogenicity

**Question**: Do pathogenic strains have different prophage burden?

**Stratify by**:
- Ribotype (e.g., 027, 078 - hypervirulent)
- Toxin genes (tcdA, tcdB)
- Clinical vs environmental isolates

## Oxygen Gradient Study Context

### Current Status

| Organism | Metabolism | Samples | Prophages/Genome | Status |
|----------|------------|---------|------------------|--------|
| Fusobacterium | Anaerobe | 218 | 1.3 | Complete ✓ |
| Bacteroides | Anaerobe | 1,411 | ? | Running... |
| **C. difficile** | **Anaerobe** | **?** | **?** | **Ready to launch** |
| E. coli/STEC | Facultative | 7,340 | ? | Running... |
| Salmonella | Facultative | 2,737 | 4.2 | Complete ✓ |

### Hypothesis Testing

**Prediction**: C. difficile will have LOW prophage burden

**Supports hypothesis if**:
- C. difficile < 2 prophages/genome (like Fusobacterium)
- C. difficile << E. coli (testing niche-matched comparison)
- Similar to Bacteroides (both gut anaerobes)

**Challenges hypothesis if**:
- C. difficile has high prophage burden (>4 prophages/genome)
- Similar to E. coli despite anaerobic metabolism

## Study Metadata

- **Pipeline**: COMPASS v1.2.0-candidate
- **Tools**: VIBRANT (prophage detection), DIAMOND, PHANOTATE
- **Expected runtime**: 1-2 weeks
- **Output location**: `/fastscratch/tylerdoe/clostridium_results`

## References

### C. difficile Biology
- Lawley et al. (2010) - C. difficile genome diversity
- He et al. (2010) - Epidemic C. difficile 027 genome
- Knight et al. (2015) - C. difficile evolution

### Prophage Studies
- Sekulovic et al. (2011) - C. difficile prophages and pathogenicity
- Hargreaves et al. (2014) - C. difficile phage biology
- Shan et al. (2012) - Prophages in C. difficile 027

### Oxygen-Prophage Relationship
- Goerke & Wolz (2010) - ROS and prophage induction
- Nanda et al. (2015) - Oxidative stress triggers lysogeny
- Wang et al. (2010) - Prophages and stress tolerance

---

*Part of Oxygen Gradient Prophage Burden Analysis*
*Comparative study of prophage ecology across oxygen tolerance groups*
*Created: 2026-04-15*
