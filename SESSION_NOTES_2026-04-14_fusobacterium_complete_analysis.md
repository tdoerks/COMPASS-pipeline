# Session Notes: 2026-04-14 - Fusobacterium Complete Analysis & Anaerobe Prophage Hypothesis

## Executive Summary

Completed comprehensive **Fusobacterium prophage study** (218 genomes) and discovered **novel finding**: obligate anaerobes have dramatically lower prophage burden (1.3/genome) compared to aerobic/facultative bacteria (5-12/genome). Successfully fetched and integrated metadata, revealing host-specific and niche-specific prophage patterns.

---

## 1. Fusobacterium Pipeline Results

### Study Parameters
- **Pipeline**: COMPASS 1.2.0-candidate
- **Job ID**: 7610190 (Beocat)
- **Status**: ✅ **COMPLETE**
- **Runtime**: ~7 hours
- **Location**: `/fastscratch/tylerdoe/fusobacterium_results/`
- **Archive**: `/bulk/tylerdoe/archives/fusobacterium_results/`

### Sample Statistics
- **SRA downloads attempted**: 292
- **Failed downloads**: 69 (no data available)
- **Successful downloads**: 223
- **FASTP failures**: 1 (quality filtering)
- **SPAdes assembly failures**: 4 (poor quality)
- **Final analyzed genomes**: **218**
- **Success rate**: 97.8% (218/223)

### Assembly Quality
- **Average genome size**: ~3.3 Mb (typical for Fusobacterium)
- **Average GC content**: 29-30% (confirms Fusobacterium)
- **BUSCO completeness**: 97.6% (bacteria_odb10)
- **High quality assemblies**: Excellent data

---

## 2. Prophage Analysis Results

### Overall Prophage Burden
- **Total prophages detected**: 278 (VIBRANT integrated prophages)
- **Genomes with prophages**: 140 (64%)
- **Genomes without prophages**: 78 (36%) ⬅️ **Unusually high**
- **Average prophages/genome**: **1.3** ⬅️ **Very low**

### Prophage Distribution
| Prophage Count | Samples | Percentage |
|----------------|---------|------------|
| 0 prophages | 78 | 36% |
| 1 prophage | 52 | 24% |
| 2 prophages | 56 | 26% |
| 3 prophages | 20 | 9% |
| 4 prophages | 9 | 4% |
| 5-7 prophages | 3 | 1% |

### Prophage Characteristics
- **Size range**: 5.8 kb - 180 kb
- **Average size**: 38.4 kb (typical lambdoid phage)
- **Size distribution**:
  - Small prophages (<20 kb): 85 (31%)
  - Medium prophages (20-50 kb): 148 (53%)
  - Large prophages (>50 kb): 46 (17%)

### Prophage Proteins
- **Total DIAMOND hits**: 5,469
- **Average hits per genome**: 25
- **Most common prophage genes**: Terminase, integrase, structural proteins

---

## 3. Metadata Analysis

### Metadata Acquisition
- **Script**: `scripts/fetch_sra_metadata.py`
- **Runtime**: ~15 minutes (217/218 samples)
- **NCBI fields retrieved**: 90+ metadata fields
- **Output**: `data/fusobacterium_metadata.tsv`

### Key Metadata Fields (Sample Coverage)

**Host & Source:**
- `host`: 165/217 samples (76%)
- `isolation_source`: 96/217 samples (44%)
- `geo_loc_name`: 171/217 samples (79%)
- `sub_species`: 81/217 samples (37%)
- `strain`: 213/217 samples (98%)

**Context:**
- `collection_date`: 168/217 samples (77%)
- `host_disease`: 13/217 samples (6%)
- `biotic_relationship`: 8/217 samples (4%)
- `env_broad_scale`: 113/217 samples (52%)

### Host Distribution
| Host | Count | % |
|------|-------|---|
| Homo sapiens (Human) | 98 | 45% |
| Bos taurus (Cattle) | 49 | 23% |
| Unknown | 52 | 24% |
| Sus scrofa (Pig) | 4 | 2% |
| Gallus gallus (Chicken) | 3 | 1% |
| Others (dog, alpaca, vulture, monkey) | 11 | 5% |

### Subspecies Distribution
| Subspecies | Count |
|------------|-------|
| F. funduliforme | 46 |
| F. animalis | 19 |
| F. nucleatum | 10 |
| F. necrophorum | 6 |
| Unknown | 136 |

### Isolation Sources (Where Available)
- **Oral cavity**: 9 samples (saliva, dental plaque, oral)
- **GI tract**: 19 samples (stool, colon, feces, ileum, caecum)
- **Clinical infections**: Blood cultures, abscesses, ulcers
- **Liver**: 1 sample (F. necrophorum liver abscess)
- **Other**: Laboratory strains, environmental

---

## 4. Prophage-Metadata Associations

### Analysis 1: Prophage Load by Host Species

| Host | n | Mean Prophages | Std Dev |
|------|---|----------------|---------|
| **Sus scrofa (Pig)** | 4 | **3.25** | 0.96 |
| **Bos taurus (Cattle)** | 49 | **1.45** | 1.08 |
| Gallus gallus (Chicken) | 3 | 1.33 | 0.58 |
| **Homo sapiens (Human)** | 98 | **1.09** | 1.20 |
| Not applicable | 4 | 1.00 | 0.82 |

**Key Finding**: Pigs have highest prophage burden (3.25), cattle intermediate (1.45), humans lowest (1.09)

**Statistical Test**: Human vs Bovine
- t-test: t=-1.818, p=0.0720
- Not statistically significant (trend toward higher in cattle)

### Analysis 2: Prophage Load by Subspecies

| Subspecies | n | Mean Prophages | Std Dev |
|------------|---|----------------|---------|
| **F. necrophorum** | 6 | **2.00** | 1.55 |
| F. funduliforme | 46 | 1.37 | 1.02 |
| F. animalis | 19 | 1.16 | 1.71 |
| F. nucleatum | 10 | 0.30 | 0.48 |

**Key Finding**: F. necrophorum (cattle liver pathogen) has highest prophage burden (2.0), F. nucleatum (oral) has lowest (0.3)

### Analysis 3: Prophage Load by Body Site

**Isolation Source** (limited data):
| Source | n | Mean Prophages |
|--------|---|----------------|
| **Human stool** | 6 | **2.50** |
| **Colon biopsy** | 7 | **2.43** |
| **Oral cavity** | 2 | **2.50** |
| Feces | 2 | 2.00 |
| Saliva | 3 | 1.33 |
| Blood culture | 3 | 0.00 |
| Laboratory | 4 | 0.00 |

**Broader Categories**:
- **GI tract** (n=19): 2.11 ± 1.29 prophages
- **Oral cavity** (n=9): 1.22 ± 0.97 prophages

**Key Finding**: GI tract isolates have MORE prophages than oral (2.11 vs 1.22) - opposite of expectation!

### Analysis 4: F. necrophorum Specific

**Your professor's focus organism:**
- Samples: 6
- Prophage load: 2.00 ± 1.55
- Hosts: 5 cattle (Bos taurus), 1 unknown
- Isolation source: Unknown (metadata missing)
- **Higher than average** prophage burden

---

## 5. NOVEL HYPOTHESIS: Oxygen-Dependent Prophage Burden

### The Discovery

**Fusobacterium (obligate anaerobe)** has dramatically **lower prophage burden** than aerobic/facultative bacteria:

| Organism | Metabolism | Prophages/Genome | Source |
|----------|------------|------------------|--------|
| **Fusobacterium** | **Obligate anaerobe** | **1.3** | **This study (n=218)** |
| E. coli | Facultative | 8.2 | Literature (n=58) |
| Salmonella | Facultative | 5.6 | Literature (n=27) |
| Salmonella | Facultative | 4.2 | Your temporal study (n=2,737) |
| P. aeruginosa | Aerobic | 11-12 | Literature |
| Vibrio | Facultative | 3-4 | Your study |

### Hypothesis

**"Prophage burden correlates inversely with anaerobic lifestyle due to lack of oxidative stress-driven lysogeny selection"**

### Supporting Evidence from Literature (2023-2025)

#### 1. Oxidative Stress Triggers Prophage Induction
- **2025 study**: ROS activates OxyR → prophage Pf4 production in P. aeruginosa
- Oxidative stress model governs lysogenic/lytic switch
- Prophages transition to lytic cycle under environmental stress

#### 2. Prophages Provide Oxidative Stress Tolerance
- Lysogenic phages enhance survival under ROS/RNS
- Prophage phi456 regulates oxidative stress response genes
- Prophages help bacteria survive oxidative stress and acidic conditions

#### 3. Anaerobes Lack Oxidative Stress Pressure
- **Fusobacterium** (obligate anaerobe) doesn't face ROS
- No selective advantage for prophage-mediated ROS tolerance
- **Result**: Lower prophage acquisition/retention

#### 4. Gap in Literature
- **No direct comparative study** exists across oxygen tolerance groups
- Studies focus on individual species or stress-induced induction
- **Missing**: Systematic comparison of aerobes vs facultative vs anaerobes

### Novel Contribution

**First study** to propose and document oxygen-dependent prophage burden across bacterial lifestyles.

---

## 6. Proposed Comparative Study: "Prophage Burden Across the Oxygen Gradient"

### Study Design

**Hypothesis**: Prophage burden decreases with obligate anaerobic lifestyle

**Study Groups** (n=200-500 genomes each):

#### Group 1: Obligate Aerobes (Expected: 8-12 prophages/genome)
- Mycobacterium tuberculosis
- Pseudomonas aeruginosa (partial data available)
- Bacillus subtilis (aerobic)

#### Group 2: Facultative Anaerobes (Expected: 5-8 prophages/genome)
- ✅ E. coli (STEC study - 7,340 genomes in progress)
- ✅ Salmonella (completed - 2,737 genomes)
- ✅ Vibrio (completed)

#### Group 3: Microaerophiles (Expected: 3-4 prophages/genome)
- Campylobacter jejuni
- Helicobacter pylori

#### Group 4: Obligate Anaerobes (Expected: 1-2 prophages/genome)
- ✅ **Fusobacterium** (completed - 218 genomes)
- Bacteroides fragilis (gut anaerobe) ⬅️ **NEXT**
- Clostridium difficile
- Prevotella (oral anaerobe)

### Analysis Metrics
- Prophages per genome (mean ± SD)
- % genomes with prophages
- Prophage size distribution
- Prophage gene content (oxidative stress response genes?)

### Statistical Analysis
- ANOVA across oxygen tolerance groups
- Linear regression: prophage burden ~ oxygen requirement
- Control for: genome size, phylogenetic distance

### Expected Timeline
- **Weeks 1-2**: Bacteroides, Clostridium, Prevotella (3 anaerobes)
- **Weeks 3-4**: Campylobacter, Helicobacter (2 microaerophiles)
- **Weeks 5-6**: Mycobacterium (1 obligate aerobe)
- **Week 7**: Comparative analysis, manuscript preparation

---

## 7. Future Fusobacterium Analyses

### Immediate Opportunities (Ready to Run)

#### A. Geographic Patterns
- **Data**: 171/217 samples with geo_loc_name
- **Question**: Are certain regions prophage hotspots?
- **Approach**: Group by country, compare prophage burden
- **Countries**: Vietnam, China, USA, Hong Kong, Europe

#### B. Temporal Trends
- **Data**: 168/217 samples with collection_date (2017-2019+)
- **Question**: Is prophage burden changing over time?
- **Approach**: Plot prophage count vs year, linear regression

#### C. Prophage Size vs Metadata
- **Data**: prophage_regions.tsv + metadata
- **Questions**:
  - Do bovine isolates have larger prophages?
  - Do oral vs GI prophages differ in size?
  - Host-specific prophage size patterns?

#### D. Clinical vs Commensal
- **Data**: biotic_relationship field (8 samples marked "commensal")
- **Question**: Do pathogenic strains have more prophages?
- **Limited data** but worth exploring

#### E. Multi-Factor Analysis
- **Combine**: Host + Subspecies + Body site
- **Example**: "Human F. nucleatum from oral" vs "Bovine F. necrophorum from liver"
- **Statistical**: ANOVA with multiple factors

#### F. Assembly Quality Correlations
- **Merge**: assembly_stats.tsv with prophage data
- **Questions**:
  - Does genome size correlate with prophage count?
  - GC content vs prophage burden?
  - Genome completeness vs prophage detection?

### Advanced Analyses (Require Setup)

#### G. Phylogenomic Analysis
**Goal**: Compare prophage evolution vs host evolution

**Approach**:
1. Extract all prophage sequences (from VIBRANT .fna files)
2. Align prophage sequences (MAFFT)
3. Build prophage tree (FastTree/RAxML)
4. Build host genome tree (core genes)
5. Compare trees: Vertical inheritance vs horizontal transfer

**Files Available**:
- `vibrant/SRR*_vibrant/*_contigs.phages_combined.fna` (prophage sequences)
- `phanotate/` (prophage ORF annotations)
- `assemblies/` (host genomes)

**Questions**:
- Do prophages cluster by host species or transfer between species?
- F. necrophorum prophages: unique or shared with other Fusobacterium?

#### H. Prophage Functional Analysis
**Goal**: Characterize prophage genes

**Approach**:
1. Extract PHANOTATE annotations
2. Identify conserved prophage markers (terminase, integrase)
3. Look for cargo genes (toxins, AMR, virulence)

**Files Available**:
- `phanotate/*.txt` (219 samples)
- `diamond_prophage/*.tsv` (prophage protein hits)

#### I. Prophage-AMR Intersection
**Goal**: Do prophages carry resistance/virulence genes?

**Approach**:
1. Analyze `prophage_amr/*.tsv` (624 files)
2. Identify genes at prophage-AMR intersection
3. Compare prophage-associated genes vs chromosome

**Files Available**:
- `prophage_amr/SRR*_prophage_amr.tsv` (218 samples, mostly headers)

#### J. Plasmid-Prophage Comparison
**Goal**: Do plasmids compensate for low prophage burden?

**Approach**:
1. Extract MOB-suite results
2. Compare plasmid prevalence vs prophage count
3. Do prophage-poor genomes have more plasmids?

**Files Available**:
- `mobsuite/SRR*/` (218 samples)

---

## 8. Analysis Files Created

### Location: `/fastscratch/tylerdoe/fusobacterium_results/analysis/`

| File | Description | Size |
|------|-------------|------|
| `fusobacterium_prophage_summary.txt` | Comprehensive summary statistics | 220 B |
| `prophage_counts_per_sample.tsv` | Prophage burden per genome | 2.9 KB |
| `all_prophage_regions.tsv` | Prophage coordinates and sizes | 31 KB |
| `assembly_stats.tsv` | GC%, length, contigs | - |
| `bacterial_lineages.tsv` | BUSCO lineage assignments | - |
| `prophage_amr_analysis.txt` | Prophage-AMR associations | - |
| `prophage_proteins.txt` | Top prophage proteins | - |
| `cross_study_comparison.txt` | Comparison to other bacteria | - |
| `phylogenomics_plan.txt` | Future phylogenetic analysis plan | - |

### Location: `fusobacterium_necrophorum_study/data/`

| File | Description |
|------|-------------|
| `fusobacterium_metadata.tsv` | NCBI SRA metadata (217 samples) |
| `fusobacterium_metadata_prophage_merged.tsv` | Merged metadata + prophage counts |

---

## 9. Scripts Created

### Location: `fusobacterium_necrophorum_study/scripts/`

#### `fetch_fusobacterium_necrophorum.py`
- **Purpose**: Download Fusobacterium SRA accessions from NCBI
- **Query**: All Fusobacterium species (not just F. necrophorum)
- **Output**: 292 accessions

#### `create_samplesheet.py`
- **Purpose**: Generate COMPASS samplesheet
- **Input**: SRA accessions
- **Output**: `data/samplesheet_stec.txt`

#### `fetch_sra_metadata.py`
- **Purpose**: Fetch isolation source, host, geography from NCBI
- **Runtime**: ~15 minutes for 218 samples
- **Rate limiting**: 0.4s between requests
- **Output**: `data/fusobacterium_metadata.tsv`

#### `merge_metadata_prophage.py`
- **Purpose**: Merge metadata with prophage counts, run statistical analyses
- **Analyses**:
  - Prophage load by host species
  - Prophage load by subspecies
  - Prophage load by isolation source
  - Human vs Bovine t-test
  - F. necrophorum specific analysis
  - Oral vs GI tract comparison
- **Output**: `data/fusobacterium_metadata_prophage_merged.tsv`

---

## 10. STEC Study Status

### Concurrent Study
- **Pipeline**: COMPASS 1.1.0-candidate
- **Job ID**: 7614525 (Beocat)
- **Status**: Running (49% complete)
- **Progress**: 3,632 of 7,340 SRA downloads complete
- **Samples ready**: 3,521 queued for assembly
- **Expected completion**: 1-2 days

### Study Purpose
- **Organism**: E. coli (STEC - Shiga toxin-producing)
- **Sampling**: Temporal (100 samples/month, 2020-2026)
- **Total samples**: 7,340
- **Focus**: Stx prophage dynamics (Stx1, Stx2 on lambdoid prophages)
- **Expected prophages/genome**: 5-8 (facultative anaerobe)

---

## 11. Repository Status

### Current Branch
- **Branch**: `scratch`
- **Ahead of remote**: Up to date (after recent pushes)

### Files Added/Modified

#### Session Notes
- `SESSION_NOTES_2026-04-14_fusobacterium_anaerobe_hypothesis.md`
- `SESSION_NOTES_2026-04-14_fusobacterium_complete_analysis.md` (this file)

#### Fusobacterium Study
- `fusobacterium_necrophorum_study/scripts/fetch_fusobacterium_necrophorum.py`
- `fusobacterium_necrophorum_study/scripts/create_samplesheet.py`
- `fusobacterium_necrophorum_study/scripts/fetch_sra_metadata.py`
- `fusobacterium_necrophorum_study/scripts/merge_metadata_prophage.py`
- `fusobacterium_necrophorum_study/run_fusobacterium.sh`
- `fusobacterium_necrophorum_study/README.md`
- `fusobacterium_necrophorum_study/data/sra_accessions_fusobacterium_necrophorum_all.txt`

#### STEC Study
- `stec_prophage_study/scripts/fetch_stec_temporal.py`
- `stec_prophage_study/scripts/fetch_stec_all.py`
- `stec_prophage_study/scripts/create_samplesheet.py`
- `stec_prophage_study/run_stec_prophage.sh`
- `stec_prophage_study/README.md`

---

## 12. Key Findings Summary

### 1. Fusobacterium has LOW Prophage Burden
- **1.3 prophages/genome** (vs 5-12 in aerobic/facultative bacteria)
- **36% prophage-free** genomes (unusually high)
- **First obligate anaerobe** in phage study series

### 2. Host-Specific Patterns
- **Pigs**: 3.25 prophages/genome (highest)
- **Cattle**: 1.45 prophages/genome
- **Humans**: 1.09 prophages/genome (lowest)

### 3. Subspecies Variation
- **F. necrophorum**: 2.0 prophages (cattle pathogen)
- **F. nucleatum**: 0.3 prophages (oral pathogen)

### 4. Body Site Differences
- **GI tract**: 2.11 prophages (higher)
- **Oral cavity**: 1.22 prophages (lower)
- **Unexpected**: Oral should have more (biofilms)

### 5. Novel Hypothesis Proposed
- **Prophage burden inversely correlates with anaerobic lifestyle**
- Mechanism: Lack of oxidative stress selection
- No prior comparative study across oxygen tolerance groups

---

## 13. Publication Potential

### Title Ideas

1. **"Prophage Burden Inversely Correlates with Anaerobic Lifestyle: A Comparative Genomic Analysis Across Bacterial Oxygen Tolerance"**

2. **"Oxygen-Dependent Prophage Burden: First Comparative Study of Prophage Prevalence Across Aerobic, Facultative, and Anaerobic Bacteria"**

3. **"Low Prophage Burden in Fusobacterium: Evidence for Oxygen-Driven Lysogeny Selection"**

### Target Journals
- **mBio** (ASM flagship)
- **ISME Journal** (microbial ecology)
- **Microbiome** (comparative genomics)
- **Nature Communications** (novel finding)

### Manuscript Sections

**Introduction**:
- Prophages ubiquitous in bacteria
- Lysogeny provides stress tolerance (oxidative stress)
- Gap: No comparison across oxygen tolerance groups

**Methods**:
- COMPASS pipeline, VIBRANT prophage detection
- Comparative genomics across oxygen gradient
- Statistical analyses

**Results**:
1. Fusobacterium prophage burden (1.3/genome)
2. Comparison to aerobes/facultative (5-12/genome)
3. Host and niche-specific patterns
4. Oxidative stress gene enrichment in aerobe prophages?

**Discussion**:
- Oxygen-dependent prophage burden
- Oxidative stress as selective pressure for lysogeny
- Anaerobes lack this pressure → lower prophage retention
- Implications for phage therapy, microbiome engineering

---

## 14. Next Steps

### Immediate (This Week)
1. ✅ **Complete Fusobacterium analysis** - DONE
2. ✅ **Fetch and integrate metadata** - DONE
3. ✅ **Host/niche associations** - DONE
4. ⏳ **Wait for STEC completion** - In progress (49%)

### Short-Term (Next 2 Weeks)
1. **Launch Bacteroides fragilis study** (obligate anaerobe, gut)
   - Most abundant gut anaerobe
   - Same niche as E. coli but anaerobic
   - Perfect comparison

2. **Launch Clostridium difficile** (obligate anaerobe, clinical)
   - Clinically important
   - Well-studied organism
   - ~1000+ genomes available

3. **Launch Prevotella** (obligate anaerobe, oral/gut)
   - Oral microbiome anaerobe
   - Compare to F. nucleatum (oral)

### Medium-Term (Next Month)
4. **Launch microaerophiles**:
   - Campylobacter jejuni
   - Helicobacter pylori

5. **Launch obligate aerobes**:
   - Mycobacterium tuberculosis
   - Additional Pseudomonas

6. **Comparative analysis** across all groups

### Long-Term (Next 2-3 Months)
7. **Phylogenomic analysis** of Fusobacterium prophages
8. **Functional analysis**: Prophage gene content differences
9. **Manuscript preparation**
10. **Data visualization** (figures for publication)

---

## 15. Technical Details

### Pipeline Versions
- **Fusobacterium**: COMPASS 1.2.0-candidate
- **STEC**: COMPASS 1.1.0-candidate
- **Salmonella** (previous): COMPASS 1.0.1

### HPC Resources
- **Cluster**: Beocat (K-State)
- **Working storage**: `/fastscratch/tylerdoe/`
- **Archive storage**: `/bulk/tylerdoe/archives/`
- **Pipeline locations**:
  - `/fastscratch/tylerdoe/COMPASS-pipeline-1.1.0-candidate/`
  - `/fastscratch/tylerdoe/COMPASS-pipeline-1.2.0-candidate/`

### Nextflow Configuration
- **Profile**: beocat
- **BUSCO database**: `/fastscratch/tylerdoe/databases/busco_downloads`
- **Prophage database**: `/fastscratch/tylerdoe/databases/prophage_db.dmnd`

### SLURM Job Settings
```bash
#SBATCH --time=336:00:00  # 14 days
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --mail-type=END,FAIL
```

---

## 16. Lessons Learned

### Technical Issues Resolved
1. **MLST failure**: Fusobacterium lacks PubMLST scheme (expected)
2. **BUSCO lineage**: Stayed at bacteria_odb10 (no Fusobacteriales database)
3. **Species ID**: Required NCBI metadata (not in pipeline output)
4. **Git remote naming**: "origin" vs "compass" confusion resolved

### Successful Strategies
1. **Metadata fetching**: Python script with NCBI eutils worked perfectly
2. **Prophage detection**: VIBRANT + DIAMOND provided comprehensive results
3. **Data integration**: Pandas merge simplified association analyses
4. **Parallel studies**: Running on different pipeline versions avoided conflicts

### Best Practices
1. **Archive early**: rsync to /bulk/ immediately after completion
2. **Exclude FASTQs**: Save storage space in archives
3. **Metadata is key**: Worth the 15-minute fetch for rich analyses
4. **Git session notes**: Document findings immediately (don't wait)

---

## 17. Contacts & Resources

### People
- **Professor**: Works on F. necrophorum (bovine liver abscesses)
- **HPC Support**: Beocat team (K-State)

### GitHub
- **Repository**: https://github.com/tdoerks/COMPASS-pipeline.git
- **Branch**: scratch
- **Issues**: Report at pipeline issues page

### Literature
- **Oxidative stress & prophages**: 2025 P. aeruginosa Pf4 study
- **Anaerobic phages**: Limited literature (gap in field)
- **Prophage burden studies**: E. coli (8.2/genome), Salmonella (5.6/genome)

---

## 18. Data Availability

### Raw Data
- **SRA accessions**: `data/sra_accessions_fusobacterium_necrophorum_all.txt` (292)
- **NCBI metadata**: `data/fusobacterium_metadata.tsv` (217)
- **COMPASS results**: `/fastscratch/tylerdoe/fusobacterium_results/`

### Processed Data
- **Prophage counts**: `analysis/prophage_counts_per_sample.tsv`
- **Prophage regions**: `analysis/all_prophage_regions.tsv`
- **Merged data**: `data/fusobacterium_metadata_prophage_merged.tsv`

### Code
- **All scripts**: `fusobacterium_necrophorum_study/scripts/`
- **SLURM job**: `fusobacterium_necrophorum_study/run_fusobacterium.sh`

---

## 19. Acknowledgments

- **COMPASS Pipeline**: Nextflow-based bacterial genomics pipeline
- **VIBRANT**: Prophage detection tool
- **NCBI SRA**: Public sequence data repository
- **Beocat HPC**: K-State computing resources
- **BUSCO**: Genome quality assessment
- **MOB-suite**: Plasmid detection
- **AMRFinder**: Resistance/virulence gene detection

---

## 20. Future Vision

### Short-Term Goal
Complete **oxygen gradient prophage study** across 6-8 bacterial species, demonstrating inverse correlation between anaerobic lifestyle and prophage burden.

### Medium-Term Goal
Publish **first comparative study** of prophage prevalence across bacterial oxygen tolerance groups, establishing new framework for understanding lysogeny evolution.

### Long-Term Impact
Establish **oxygen-dependent prophage burden** as fundamental principle in microbial ecology, with implications for:
- Phage therapy (anaerobes may be poor candidates)
- Microbiome engineering (prophage-mediated gene transfer differs by oxygen niche)
- Evolution of lysogeny (oxidative stress as major selective force)
- Anaerobic bacteria biology (different mobile genetic element strategies)

---

*Session conducted: 2026-04-14*
*Analysis by: Tyler Doerks*
*Pipeline: COMPASS 1.2.0-candidate*
*Study: Fusobacterium prophage dynamics*

**Status: COMPLETE ✓**
