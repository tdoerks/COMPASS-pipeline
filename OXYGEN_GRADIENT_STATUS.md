# Oxygen Gradient Prophage Burden Study - Status

**Updated**: 2026-04-15

## Hypothesis

**Oxygen-dependent prophage burden**: Bacteria exposed to oxygen have higher prophage burden due to oxidative stress-driven selection for prophage-mediated stress tolerance genes.

**Prediction**: Obligate anaerobes << Microaerophiles < Facultative anaerobes < Obligate aerobes

---

## Study Status Overview

### ✅ Complete Studies

| Organism | Metabolism | Niche | Samples | Prophages/Genome | Status |
|----------|------------|-------|---------|------------------|--------|
| **Fusobacterium** | Obligate anaerobe | Oral/GI | 218 | **1.3** | Complete ✓ |
| **Salmonella** | Facultative | GI | 2,737 | **4.2** | Complete ✓ |

**Key finding**: Fusobacterium (anaerobe) has 3.2× lower prophage burden than Salmonella (facultative)

---

### 🔄 Running Studies

| Organism | Metabolism | Niche | Samples | Job ID | Progress | Status |
|----------|------------|-------|---------|--------|----------|--------|
| **Bacteroides fragilis** | Obligate anaerobe | Gut | 1,411 | 7643548 | 236/1411 (17%) | Downloading... |
| **E. coli/STEC** | Facultative | Gut | 7,340 | 7614525 | 98% DL, 42% QC | Assembling... |

**Expected**:
- Bacteroides: LOW burden (1-2) like Fusobacterium
- E. coli: HIGH burden (6-10) like Salmonella

---

### 📋 Ready to Launch

| Organism | Metabolism | Niche | Samples | Setup | Launch Command |
|----------|------------|-------|---------|-------|----------------|
| **Clostridium difficile** | Obligate anaerobe | Gut | **9,133** | ✓ Complete | `sbatch clostridium_difficile_study/run_clostridium.sh` |

**Critical test**: C. difficile vs E. coli
- Same niche (gut)
- Different oxygen tolerance
- If C. difficile << E. coli → Strong support for hypothesis

---

### 📝 Planned Studies

#### Obligate Anaerobes
- **Prevotella** (oral/gut anaerobe)
  - Complement to Fusobacterium
  - Oral niche comparison
  - Expected: LOW burden

#### Microaerophiles (0.2-10% O₂)
- **Campylobacter jejuni** (GI pathogen)
  - Intermediate oxygen tolerance
  - Expected: MEDIUM burden (2-4)

- **Helicobacter pylori** (stomach pathogen)
  - Microaerophilic metabolism
  - Expected: MEDIUM burden (2-4)

#### Obligate Aerobes
- **Mycobacterium tuberculosis** (respiratory pathogen)
  - Obligate aerobe
  - Expected: HIGH burden (8-12)

- **Pseudomonas aeruginosa** (opportunistic)
  - Obligate aerobe
  - Literature: 11-12 prophages/genome
  - Expected: HIGH burden

---

## Current Progress

### Oxygen Tolerance Groups

```
Obligate Anaerobes:
├─ ✅ Fusobacterium (218 samples) → 1.3 prophages
├─ 🔄 Bacteroides (1,411 samples) → Running
└─ 📋 Clostridium (9,133 samples) → Ready

Microaerophiles:
├─ 📝 Campylobacter → Planned
└─ 📝 Helicobacter → Planned

Facultative Anaerobes:
├─ ✅ Salmonella (2,737 samples) → 4.2 prophages
└─ 🔄 E. coli/STEC (7,340 samples) → Running

Obligate Aerobes:
├─ 📝 Mycobacterium → Planned
└─ 📝 Pseudomonas → Planned
```

### Sample Size Summary
- **Total samples acquired**: 20,839
- **Completed**: 2,955 (Fusobacterium + Salmonella)
- **Running**: 8,751 (Bacteroides + STEC)
- **Ready**: 9,133 (Clostridium)
- **Planned**: ~3,000-5,000 (remaining 4 organisms)

---

## Key Comparisons

### 1. Niche-Matched: Gut Bacteria

| Organism | Oxygen | Samples | Expected Prophages | Status |
|----------|--------|---------|-------------------|--------|
| C. difficile | Anaerobe | 9,133 | 1-2 | Ready |
| Bacteroides | Anaerobe | 1,411 | 1-2 | Running |
| E. coli | Facultative | 7,340 | 6-10 | Running |
| Salmonella | Facultative | 2,737 | 4.2 ✓ | Complete |

**Critical test**: Do gut anaerobes have lower burden than gut facultatives?

### 2. Metabolism-Matched: Facultative Anaerobes

| Organism | Niche | Samples | Expected | Status |
|----------|-------|---------|----------|--------|
| E. coli | Gut | 7,340 | 6-10 | Running |
| Salmonella | Gut | 2,737 | 4.2 ✓ | Complete |

### 3. Oral vs Gut Anaerobes

| Organism | Niche | Samples | Prophages | Status |
|----------|-------|---------|-----------|--------|
| Fusobacterium | Oral/GI | 218 | 1.3 | Complete |
| Prevotella | Oral | ? | ? | Planned |
| Bacteroides | Gut | 1,411 | ? | Running |
| C. difficile | Gut | 9,133 | ? | Ready |

---

## Next Steps

### Immediate (This Week)
1. ✓ Complete Fusobacterium prophage tree (MAFFT running)
2. Monitor Bacteroides and STEC progress
3. **Launch Clostridium study** (largest dataset - 9,133 samples)

### Short-term (Next 2 Weeks)
1. Analyze Bacteroides results (compare to Fusobacterium)
2. Analyze STEC results (compare to Salmonella)
3. Wait for Clostridium downloads to complete

### Medium-term (Next Month)
1. Create Prevotella study (obligate anaerobe #4)
2. Create Campylobacter study (microaerophile #1)
3. Create Helicobacter study (microaerophile #2)
4. Analyze Clostridium vs E. coli comparison

### Long-term (Publication)
1. Create Mycobacterium study (obligate aerobe)
2. Create Pseudomonas study (obligate aerobe)
3. Statistical analysis across all groups
4. Write manuscript with oxygen gradient findings

---

## Expected Outcomes

### If Hypothesis is Supported

**Pattern**:
```
Obligate anaerobes:     1-2 prophages/genome
Microaerophiles:        2-4 prophages/genome
Facultative anaerobes:  4-6 prophages/genome
Obligate aerobes:       8-12 prophages/genome
```

**Interpretation**: Oxygen exposure drives prophage burden through:
- Oxidative stress selection
- Prophage-encoded stress tolerance genes
- Higher mutation/recombination rates
- More active phage ecology in aerobic environments

### If Hypothesis is Challenged

**Alternative patterns**:
- No oxygen correlation (niche or taxonomy drives burden)
- Reverse pattern (anaerobes have MORE prophages)
- No consistent pattern across groups

---

## Publication Status

### Current Evidence
- ✅ Fusobacterium: 1.3 prophages/genome (low burden documented)
- ✅ Host/niche associations identified
- 🔄 Phylogenetic analysis (tree building)
- 🔄 Bacteroides comparison (running)
- 🔄 E. coli comparison (running)

### Needed for Publication
- Complete all 3 anaerobe studies (Fusobacterium, Bacteroides, Clostridium)
- Complete facultative comparison (E. coli + Salmonella)
- At least 1-2 microaerophiles
- At least 1 obligate aerobe
- Statistical tests across oxygen groups
- Compare to literature data

### Target Timeline
- **Draft**: 2-3 months (after core studies complete)
- **Submission**: 4-5 months
- **Publication**: 6-9 months

---

## Resources

### Pipeline
- COMPASS pipeline v1.0.1, v1.1.0, v1.2.0-candidate
- Nextflow workflow
- Running on Beocat HPC (Kansas State University)

### Key Tools
- **VIBRANT**: Prophage detection
- **DIAMOND**: Protein search
- **PHANOTATE**: ORF annotation
- **MAFFT/FastTree**: Phylogenetics

### Documentation
- Session notes: Multiple detailed documentation files
- Study-specific READMEs for each organism
- Phylogenomics pipeline documentation

---

*Oxygen Gradient Prophage Burden Analysis*
*Comparative genomics across bacterial oxygen tolerance groups*
*Updated: 2026-04-15*
