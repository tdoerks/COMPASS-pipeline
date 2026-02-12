# ETEC Reference Genome Validation Plan

Validation of COMPASS pipeline using 8 well-characterized ETEC (Enterotoxigenic E. coli) reference genomes from published literature.

## Reference

**Paper**: Long-read-sequenced reference genomes of the seven major lineages of enterotoxigenic Escherichia coli (ETEC) circulating in modern time

**DOI**: https://doi.org/10.1038/s41598-021-88316-2

**Authors**: von Mentzer et al. (2021), Scientific Reports

**Description**: PacBio long-read sequenced complete genomes of 8 ETEC strains representing the 7 major ETEC lineages (L1-L7). Each genome includes manually curated chromosome and plasmids.

---

## Strains Included

| Strain | Lineage | MLST | O Antigen | Plasmids | Toxins | Colonization Factors | Location | Year |
|--------|---------|------|-----------|----------|--------|----------------------|----------|------|
| E925 | L1 | ST2353 | O6 | 4 | LT + STh | CS1 + CS3 + CS21 | Guatemala | 2003 |
| E1649 | L2 | ST4 | O6 | 4 | LT + STh | CS2 + CS3 + CS21 | Indonesia | 1997 |
| E36 | L3 | ST173 | O78 | 2 | LT + STh | CFA/I + CS21 | Bangladesh | 1980 |
| E2980 | L3 | ST5305 | O114 | 3 | LT | CS7 | Bangladesh | 2010 |
| E1441 | L4 | ST1312 | O25 | 2 | LT | CS6 + CS21 | Kenya | 1997 |
| E1779 | L5 | ST443 | O115 | 4 | LT + STh | CS5 + CS6 | Bangladesh | 2005 |
| E562 | L6 | ST2332 | ON3 | 5 | STh | CFA/I + CS21 | Mexico | 2000 |
| E1373 | L7 | ST182 | O169 | 2 | STp | CS6 | Indonesia | 1996 |

**Total**: 8 strains, 7 lineages, 26 plasmids total

---

## Validation Objectives

### Primary Objectives

1. **Plasmid Detection Accuracy**
   - Validate MOBsuite can correctly identify plasmid count
   - Expected: 2-5 plasmids per strain (as per paper)
   - Test: Compare detected plasmid count to manually curated plasmid sequences

2. **MLST Typing Accuracy**
   - Validate mlst correctly assigns sequence types
   - Expected: Specific STs for each strain (ST2353, ST4, ST173, etc.)
   - Test: Compare detected ST to paper-reported ST

### Secondary Objectives

3. **AMR Gene Detection**
   - ETEC strains may carry AMR genes (not primary focus of original paper)
   - Validate AMRFinder detects resistance genes on plasmids and chromosome
   - Test: Compare to literature-reported AMR for ETEC

4. **Prophage Detection**
   - Validate VIBRANT can identify prophages in ETEC genomes
   - Test: Check for reasonable prophage counts (expected 0-10)

5. **Assembly Quality**
   - Validate QUAST and BUSCO metrics
   - Expected: High quality (complete genomes with minimal fragmentation)

---

## Expected Results

### High Confidence Expectations

**Plasmid Counts** (from paper - chromosome + plasmids concatenated):

| Strain | Expected Plasmids | Validation Test |
|--------|-------------------|-----------------|
| E925 | 4 | plasmid_count = 4 ± 1 |
| E1649 | 4 | plasmid_count = 4 ± 1 |
| E36 | 2 | plasmid_count = 2 ± 1 |
| E2980 | 3 | plasmid_count = 3 ± 1 |
| E1441 | 2 | plasmid_count = 2 ± 1 |
| E1779 | 4 | plasmid_count = 4 ± 1 |
| E562 | 5 | plasmid_count = 5 ± 1 |
| E1373 | 2 | plasmid_count = 2 ± 1 |

**MLST Types** (from paper):

| Strain | Expected ST | Validation Test |
|--------|-------------|-----------------|
| E925 | ST2353 | mlst = 2353 |
| E1649 | ST4 | mlst = 4 |
| E36 | ST173 | mlst = 173 |
| E2980 | ST5305 | mlst = 5305 |
| E1441 | ST1312 | mlst = 1312 |
| E1779 | ST443 | mlst = 443 |
| E562 | ST2332 | mlst = 2332 |
| E1373 | ST182 | mlst = 182 |

---

## Data Preparation

### Genome Assembly

Each strain consists of:
- **1 chromosome** (complete, circularized)
- **2-5 plasmids** (complete, circularized)

**Our approach**: Concatenate chromosome + all plasmids into single FASTA file per strain

**Rationale**:
- Simulates typical assembly output (chromosome + plasmids in one file)
- MOBsuite can detect plasmids within concatenated assemblies
- AMRFinder scans entire assembly (chromosome + plasmids)
- More realistic for validation

### File Organization

```
data/validation/
├── etec_genomes/
│   ├── E925.fasta      (chromosome + 4 plasmids)
│   ├── E1649.fasta     (chromosome + 4 plasmids)
│   ├── E36.fasta       (chromosome + 2 plasmids)
│   ├── E2980.fasta     (chromosome + 3 plasmids)
│   ├── E1441.fasta     (chromosome + 2 plasmids)
│   ├── E1779.fasta     (chromosome + 4 plasmids)
│   ├── E562.fasta      (chromosome + 5 plasmids)
│   └── E1373.fasta     (chromosome + 2 plasmids)
├── etec_samplesheet.csv
├── etec_ground_truth.csv
└── run_etec_validation.sh
```

---

## Running the Validation

### Step 1: Submit COMPASS Job

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline

sbatch data/validation/run_etec_validation.sh
```

**Expected runtime**: 2-4 hours (8 genomes, complete assemblies)

### Step 2: Monitor Progress

```bash
# Check SLURM queue
squeue -u tylerdoe

# Monitor job output
tail -f /homes/tylerdoe/slurm-etec-validation-<jobid>.out
```

### Step 3: Review Results

```bash
# Check MultiQC report
firefox data/validation/etec_results/multiqc/multiqc_report.html

# Check individual results
ls data/validation/etec_results/amrfinder/
ls data/validation/etec_results/mobsuite/
ls data/validation/etec_results/mlst/
```

### Step 4: Run Validation Analysis

```bash
./bin/validate_compass_results.py \
    data/validation/etec_results \
    data/validation/etec_ground_truth.csv \
    --output data/validation/etec_validation_report.md
```

---

## Success Criteria

### Tier 1: Critical (Must Pass)

1. **MLST Typing**: 100% accuracy (8/8 correct STs)
2. **Plasmid Detection**: ≥75% accuracy (6/8 within ±1 plasmid)

### Tier 2: Important (Should Pass)

3. **Assembly Quality**: All genomes pass BUSCO/QUAST thresholds
4. **Pipeline Completion**: All 8 genomes process without errors

### Tier 3: Informational

5. **AMR Detection**: Reasonable AMR gene counts (0-20 per genome)
6. **Prophage Detection**: Reasonable prophage counts (0-10 per genome)

---

## Comparison to Previous Validation

### Current Validation (K-12, EC958, CFT073)

- **Genomes**: 3 well-characterized reference strains
- **Focus**: AMR detection, prophage detection, plasmid typing
- **Result**: 100% pass rate (13/13 tests)
- **Strength**: Deep validation of specific features

### ETEC Validation (8 strains)

- **Genomes**: 8 ETEC lineage representatives
- **Focus**: Plasmid detection, MLST typing
- **Expected**: High accuracy on plasmid counts and ST typing
- **Strength**: Broader validation across multiple strains/lineages

### Combined Impact

Together, these validations demonstrate COMPASS accuracy across:
- **AMR detection** (K-12, EC958, CFT073)
- **Prophage detection** (K-12)
- **Plasmid typing** (EC958, ETEC strains)
- **MLST typing** (EC958, ETEC strains)
- **Diverse strain types** (lab strains, pathogens, ETEC)

---

## Troubleshooting

### If Plasmid Counts Don't Match

**Possible reasons**:
1. MOBsuite threshold settings (adjust `--min_length` if needed)
2. Plasmid fragmentation in concatenated assembly
3. Small plasmids below detection threshold

**Solution**: Review MOBsuite output files to see which plasmids were detected/missed

### If MLST Typing Fails

**Possible reasons**:
1. Novel alleles not in mlst database
2. Assembly fragmentation at MLST loci
3. ST not in E. coli scheme

**Solution**: Check mlst output for "novel alleles" or "-" (missing loci)

---

## Citation

If using these ETEC reference genomes for validation, cite:

> von Mentzer A, et al. Long-read-sequenced reference genomes of the seven major lineages
> of enterotoxigenic Escherichia coli (ETEC) circulating in modern time.
> Sci Rep. 2021 Apr 29;11(1):9256. doi: 10.1038/s41598-021-88316-2.

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine

**Date Created**: February 11, 2026
**COMPASS Version**: v1.3-dev
**Status**: Ready for validation run
