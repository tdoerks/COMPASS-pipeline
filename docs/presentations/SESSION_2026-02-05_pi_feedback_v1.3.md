# Session Notes: PI Feedback - COMPASS v1.3 Development Priorities
## Date: February 5, 2026

## Summary

PI provided feedback on priority features for COMPASS v1.3 development and clarified publication strategy for the methods paper.

---

## Development Priorities for v1.3

### 1. AMR Hit Counting Options

**Current Limitation:**
- Summary file shows only unique AMR genes detected per genome
- Cannot distinguish between single-copy vs. multi-copy AMR genes

**Requested Feature:**
- Add option to show **total AMR hits** vs. **unique AMR genes**
- Allow users to identify genomes with duplicate/multi-copy resistance genes

**Use Case:**
- Some AMR genes are present in multiple copies (chromosomal + plasmid)
- Gene duplications may indicate higher resistance levels
- Important for transmission studies (track copy number variation)

**Implementation Notes:**
```
Current output:
sample_id, unique_amr_genes, amr_gene_list

Proposed output:
sample_id, unique_amr_genes, total_amr_hits, amr_gene_list, amr_hit_details

Example:
Sample123, 5, 7, "blaTEM-1,sul1,tet(A),aph(3')-Ia,dfrA1", "blaTEM-1(2),sul1(1),tet(A)(1),aph(3')-Ia(2),dfrA1(1)"
```

**Files to Modify:**
- `bin/summarize_results.py` (or equivalent summary script)
- Add `--count-mode [unique|total|both]` parameter
- Default: `both` (show both columns)

**Priority:** High (needed for publication validation)

---

### 2. Sample-Level Traceability

**Current Limitation:**
- Summary file aggregates statistics but doesn't link back to source samples
- Difficult to trace specific AMR genes/prophages/MLST types to individual samples

**Requested Feature:**
- Add cross-reference file mapping summary statistics to sample IDs
- Enable tracing of any feature (AMR gene, prophage, MLST type) back to source

**Use Case:**
- "Which samples carry blaCTX-M?" → Quick lookup
- "Show me all ST131 E. coli isolates" → Direct sample list
- Validate unusual findings (e.g., rare AMR-prophage associations)

**Implementation Notes:**
```
New output files:
results/summary/amr_sample_mapping.tsv
results/summary/prophage_sample_mapping.tsv
results/summary/mlst_sample_mapping.tsv
results/summary/plasmid_sample_mapping.tsv

Format (amr_sample_mapping.tsv):
gene_name       sample_id       contig  start   end     identity        coverage
blaTEM-1        Sample001       contig_1        1234    2345    99.5    100.0
blaTEM-1        Sample042       contig_3        5678    6789    98.2    100.0
blaCTX-M-15     Sample123       contig_2        9012    10123   100.0   100.0
```

**Files to Create:**
- `bin/create_sample_mappings.py` (new script)
- Integrate into main workflow after summary generation

**Priority:** High (critical for manuscript Methods section)

---

### 3. Pipeline Validation with Known Genomes

**Current Status:**
- Pipeline tested on large datasets (E. coli, Salmonella, Campylobacter)
- No formal validation against reference genomes with known features

**Requested Feature:**
- Run COMPASS on well-characterized reference genomes
- Calculate sensitivity, specificity, precision for each module
- Document performance in Methods section

**Validation Dataset Requirements:**

#### **AMR Validation:**
- ATCC reference strains with known resistance profiles
- FDA-ARGOS database genomes (manually curated AMR annotations)
- Test strains: blaCTX-M, blaNDM, mcr-1, etc.

#### **Prophage Validation:**
- E. coli K-12 substrain with lambda prophage (well-annotated)
- P. aeruginosa PAO1 (multiple known prophages)
- Salmonella genomes with Gifsy-1/Gifsy-2 prophages

#### **Plasmid Validation:**
- IncF plasmids (well-characterized replicons)
- Known conjugative plasmids (RP4, R388, etc.)
- pUC19, pBR322 (common cloning vectors)

**Metrics to Calculate:**
```
Sensitivity = TP / (TP + FN)  # True positive rate
Specificity = TN / (TN + FP)  # True negative rate
Precision = TP / (TP + FP)    # Positive predictive value

Where:
TP = True positives (correctly detected features)
FP = False positives (incorrectly detected features)
TN = True negatives (correctly rejected non-features)
FN = False negatives (missed known features)
```

**Output:**
- `docs/validation/validation_report.md`
- Tables: AMR sensitivity (95%+), prophage precision (90%+), plasmid recall (85%+)
- Include in supplementary material for Paper 1

**Priority:** Critical (required before publication)

**Timeline:** 2-4 weeks

---

### 4. Background Genomes for Molecular Clock Study

**Purpose:**
- Curate diverse background genome dataset for temporal phylogenetic analyses
- Calibrate molecular clock for prophage evolution studies
- Provide temporal/geographic context for Kansas surveillance data

**Requirements:**

#### **Temporal Coverage:**
- Minimum: 2015-2025 (10 years)
- Ideal: 2010-2025 (15 years)
- Include at least 50 genomes per year

#### **Geographic Coverage:**
- United States: All regions (Northeast, South, Midwest, West)
- International: Europe, Asia, South America (for global context)
- Avoid over-sampling from single outbreak

#### **Clonal Diversity:**
- Include major E. coli sequence types (ST131, ST95, ST69, etc.)
- Avoid clonal expansions (no >5% from single ST per year)
- Quality filter: BUSCO >95%, N50 >100kb

**Data Sources:**
- NCBI SRA: Public E. coli WGS (filtered by year, geography)
- NARMS: Multi-year surveillance (non-Kansas to avoid overlap)
- GenomeTrakr: FDA pathogen surveillance
- EnteroBase: Curated E. coli genome database

**Output:**
```
data/background_genomes/
├── background_metadata.tsv (sample, year, country, ST, source)
├── background_assemblies/
│   ├── sample001.fasta
│   ├── sample002.fasta
│   └── ...
└── background_qc_report.html (BUSCO, N50, contamination stats)
```

**Use Cases:**
1. Molecular clock calibration (mutations per year)
2. Temporal phylogenies (root-to-tip regression)
3. Geographic spread analysis (phylogeography)
4. Baseline AMR prevalence (compare Kansas to global)

**Priority:** Medium (needed for Paper 2, not Paper 1)

**Timeline:** 1-2 months (can run in parallel with validation)

---

### 5. Publication Strategy - Paper 1 (Methods)

**Scope:** COMPASS pipeline methods and validation paper

**Key Message:** "COMPASS is a validated, scalable pipeline for integrated AMR-prophage analysis"

**Required Components:**

#### **1. Tool Description**
- Nextflow architecture
- Module descriptions (AMRFinder, VIBRANT, MLST, MOB-suite, etc.)
- Input/output formats
- Resource requirements (runtime, memory)
- Availability: GitHub + Zenodo DOI

#### **2. Validation Results**
- Reference genome testing (Feature 3 above)
- Sensitivity/specificity tables for:
  - AMR detection (vs. manual curation)
  - Prophage detection (vs. known prophages)
  - Plasmid typing (vs. known replicons)
- Inter-database concordance (AMRFinder vs. CARD vs. ResFinder)

#### **3. Demonstration Dataset (Small Novel Genomes)**
- **NOT** a large surveillance study (that's Paper 2)
- Small proof-of-concept: 50-100 genomes
- Show COMPASS capabilities:
  - AMR detection
  - Prophage-AMR integration
  - Phylogenetic analysis
  - MultiQC reporting
- Example: "Kansas E. coli 2023 subset (n=100)"

**What Paper 1 is NOT:**
- ❌ Large-scale surveillance findings (7,000+ genomes)
- ❌ Epidemiological trends over time
- ❌ Public health implications

**Those go in Paper 2:** "Kansas surveillance study with prophage-AMR findings"

**Target Journals:**
- Bioinformatics (Oxford)
- BMC Bioinformatics
- Microbial Genomics
- GigaScience

**Timeline:**
- Validation complete: March 2026
- Manuscript draft: April 2026
- Submission: May 2026

**Priority:** High (v1.3 release blocker)

---

## Implementation Roadmap

### Phase 1: Validation & Core Features (Current - 2 months)
1. ✅ Complete E. coli Monthly 100 run (in progress, ETA 1-2 weeks)
2. 🔄 Implement AMR hit counting options (Feature 1) - 1 week
3. 🔄 Implement sample traceability (Feature 2) - 1 week
4. 🔄 Run validation dataset (Feature 3) - 2-4 weeks
5. 🔄 Draft validation report - 1 week

### Phase 2: Paper 1 Preparation (2-3 months)
1. Select demonstration dataset (50-100 genomes)
2. Run COMPASS on demo dataset
3. Generate figures for methods paper
4. Write manuscript
5. Submit to journal

### Phase 3: Paper 2 Preparation (3-6 months, parallel)
1. Curate background genomes (Feature 4)
2. Run phylogenetic analyses (Kansas + E. coli temporal)
3. Statistical validation of prophage-AMR patterns
4. Write surveillance study manuscript

---

## Next Steps (Immediate Actions)

### This Week:
1. Create GitHub issues for Features 1-3
2. Start coding AMR hit counting options
3. Identify validation genome sources (ATCC, FDA-ARGOS)

### Next Week:
1. Implement sample traceability script
2. Download validation genomes
3. Run COMPASS on validation dataset

### Month 1-2:
1. Complete validation analysis
2. Draft validation report
3. Select demonstration dataset for Paper 1
4. Tag COMPASS v1.3 release

---

## Files to Create/Modify

### New Files:
- `bin/create_sample_mappings.py` (Feature 2)
- `docs/validation/validation_report.md` (Feature 3)
- `docs/validation/reference_genomes.tsv` (Feature 3)
- `data/background_genomes/background_metadata.tsv` (Feature 4)

### Modified Files:
- `bin/summarize_results.py` (Feature 1 - add hit counting)
- `nextflow.config` (add validation mode)
- `README.md` (document validation results)

---

## Notes

- All features prioritized for v1.3 stable release
- Validation is **critical** before Paper 1 submission
- Paper 1 is a methods paper, NOT a surveillance study
- Background genomes needed for Paper 2, not Paper 1
- Keep scope of Paper 1 small and focused on tool validation

---

## Contact

Tyler Doerks - tdoerks@vet.k-state.edu
Kansas State University College of Veterinary Medicine
Diagnostic Medicine/Pathobiology

---

**Last Updated**: February 5, 2026
**Branch**: `presentation` (documentation), `v1.3-dev` (implementation)
**Status**: Planning phase, implementation starting this week
