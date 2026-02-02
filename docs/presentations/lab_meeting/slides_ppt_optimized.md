# COMPASS Pipeline: Technical Deep Dive
## Lab Meeting Presentation

Tyler Doerks
Kansas State University College of Veterinary Medicine
Diagnostic Medicine/Pathobiology

Date: TBD

---

## Slide 1: Overview

### Today's Topics
1. COMPASS pipeline architecture & implementation
2. Kansas multi-organism surveillance (detailed methods)
3. E. coli temporal study (2021-2024)
4. Phylogenetic analysis technical details
5. Computational performance & challenges
6. Next steps & collaboration opportunities

**Duration**: ~45-50 minutes + discussion

---

## Slide 2A: COMPASS Pipeline - Nextflow Architecture

### Workflow Manager: Nextflow DSL2

**Why Nextflow?**
- Portable (Docker/Singularity containers)
- Resumable (caching of completed tasks)
- Scalable (local, HPC, cloud)
- Reproducible workflows
- Language-agnostic tool integration

---

## Slide 2B: Container & Resource Management

### Container Strategy
- All tools containerized (Singularity on HPC)
- Base images: BioContainers from Quay.io
- Custom containers for COMPASS-specific scripts

### Resource Management
- Dynamic resource allocation
- Process-specific CPU/memory requests
- Automatic retry on failure
- Parallel execution where possible

---

## Slide 3A: Pipeline Diagram

### ![Pipeline](../../pipeline_diagram/compass_pipeline.png)

**Key Workflow Stages**:
- Input → QC → Assembly
- AMR Detection → Prophage Analysis
- Typing → Aggregation

---

## Slide 3B: Pipeline Modules & Dependencies

### Module Structure
```
CHECK_DATABASES
├── AMRFinder database
├── BUSCO lineage datasets
└── Prophage database (DIAMOND)

DOWNLOAD_SRA → FASTQC → FASTP
└── ASSEMBLE_SPADES
    ├── QUAST, BUSCO
    ├── AMRFINDER, ABRICATE
    ├── VIBRANT → PHANOTATE
    ├── MLST, MOBSUITE_RECON
    └── MULTIQC
```

---

## Slide 4A: Data Acquisition

### SRA Download (fasterq-dump)
- **Tool**: SRA Toolkit 3.0+
- **Settings**: `--split-files`, `--threads 4`, `--progress`
- Separates paired-end reads (R1/R2)

### QC: FASTQC 0.11.9
- Per-base quality scores
- Adapter content detection
- GC distribution

---

## Slide 4B: Read Trimming

### FASTP 0.23.2
- Adapter auto-detection
- Quality filtering (Q20 threshold)
- Length filtering (≥50 bp)
- HTML quality reports

**Parameters**:
- `--detect_adapter_for_pe`
- `--qualified_quality_phred 20`
- `--length_required 50`

---

## Slide 5A: Genome Assembly

### SPADES 3.15.5 (--isolate mode)

**Why --isolate mode?**
- Optimized for bacterial isolates (not metagenomes)
- More conservative error correction
- Better contig quality
- Single-organism assumption

**Resources**: 8 CPUs, 16GB RAM per sample

---

## Slide 5B: Assembly Quality Control

### QUAST 5.2.0 (Assembly Metrics)
- N50, L50 statistics
- Number of contigs
- Total assembly length
- Largest contig

### BUSCO 5.4.7 (Completeness)
- **Lineages**: bacteria_odb10, enterobacterales_odb10
- **Metrics**: Complete, Fragmented, Missing
- **Threshold**: >95% complete for high-quality

---

## Slide 6A: AMR Detection - AMRFinder Plus

### Strategy 1: AMRFinder Plus 3.11

**Advantages**:
- NCBI-curated, regularly updated
- Organism-specific thresholds
- Includes point mutations
- Plus mode: virulence, stress response

**Usage**: Nucleotide search with organism flag

---

## Slide 6B: AMR Detection - Multi-Database Validation

### Strategy 2: ABRICATE 1.0.1

**Five Databases**:
- NCBI: AMRFinderPlus database
- CARD: Comprehensive Antibiotic Resistance
- ResFinder: Acquired resistance genes
- ARG-ANNOT: Antibiotic Resistance Gene-ANNOTation
- VFDB: Virulence Factor Database

**Thresholds**: 75% identity, 50% coverage

---

## Slide 7A: Prophage Analysis - VIBRANT

### VIBRANT 1.2.1 (Machine Learning-based)

**How it works**:
- Neural network trained on viral/prophage genomes
- Identifies prophage regions in bacterial genomes
- Extracts complete prophage sequences
- Classifies by lifestyle (lytic vs lysogenic)

**Precision**: ~95% (literature)

---

## Slide 7B: Prophage Gene Annotation

### PHANOTATE 1.5.0

**Purpose**: Secondary annotation for prophages
- Optimized gene caller for phages
- Better than Prodigal for viral genes
- Improves downstream functional analysis

**Outputs**:
- Predicted prophage sequences (.fna)
- Translated proteins (.faa)
- Functional predictions (.tsv)

---

## Slide 8: Prophage-AMR Integration Analysis

### Custom Python Module

**Workflow**:
1. Load AMR hits from AMRFinder
2. Load prophage coordinates from VIBRANT
3. Check genomic overlap
4. Record prophage-AMR associations

**Challenges**:
- Prophage boundaries imprecise
- AMR genes at prophage edges (mobile?)
- Need stringent overlap criteria

---

## Slide 9A: Typing - MLST

### MLST 2.23.0

**Purpose**: Multi-locus sequence typing
- 7-locus allele profile
- Assigns sequence type (ST)
- Clonal lineage identification

**Databases**: Organism-specific schemes (E. coli, Salmonella, etc.)

---

## Slide 9B: Plasmid Reconstruction

### MOB-suite 3.1.4

**Plasmid Analysis**:
- Identifies plasmid contigs
- Reconstructs circular plasmids
- Types replicons
- Predicts mobility

**Why Important?**
- AMR genes often plasmid-borne
- Distinguish chromosomal vs plasmid AMR
- Plasmids facilitate horizontal transfer

---

## Slide 10: Output Aggregation & Visualization

### MultiQC 1.14
- Aggregates all module outputs
- Generates single HTML report
- Sections: FASTQC, assembly, AMR, MLST

### Custom Data Explorer
- Interactive dashboard (HTML/JavaScript)
- Search by sample, gene, ST
- Filter by organism, year, quality
- Export filtered results

---

## Slide 11A: COMPASS Datasets - E. coli Runs

### Completed E. coli Analyses

| Dataset | Samples | Date Range | Status |
|---------|---------|------------|--------|
| **E. coli 2020 NARMS** | 2,257 | 2020 | ✅ Complete |
| **Kansas E. coli 2021** | 2,403 | 2021 | ✅ Complete |
| **Kansas E. coli 2022** | 2,836 | 2022 | ✅ Complete |
| **E. coli 2023** | 3,862 | 2023 | ✅ Complete |
| **E. coli 2024** | 3,779 | 2024 | ✅ Complete |

**E. coli Total**: 15,754 samples

---

## Slide 11B: COMPASS Datasets - Multi-Organism & In Progress

### Kansas Multi-Organism (Complete)
- **829 samples**: Campylobacter (64), Salmonella (148), E. coli (617)
- **Date range**: 2021-2025
- **Status**: ✅ Complete

### In Progress
- **E. coli Monthly 100**: 7,142 samples (Jan 2020 - Jan 2026)
- **Progress**: ~30% assembled

### Grand Total: ~23,000+ samples across all COMPASS runs

---

## Slide 12A: Kansas Dataset - Sample Acquisition

### Sample Details
- **Source**: Kansas veterinary diagnostic laboratory
- **Sequencing**: Illumina (NextSeq/MiSeq)
- **Coverage**: >50X average
- **Years**: 2021-2025

### Organism Distribution
- E. coli: 617 samples (final)
- Salmonella: 148 samples (final)
- Campylobacter: 64 samples (final)

---

## Slide 12B: Kansas Dataset - Quality Filtering

### Quality Filters Applied
- Read quality: >Q20
- Assembly length: Within 80-120% of expected genome size
- BUSCO completeness: >90%
- Contamination check: <5% non-target reads

### Filtering Results
- **Submitted**: ~28,700 total samples
- **Quality-filtered**: 829 samples retained
- **Final**: 829 assembled (100% pass rate)

---

## Slide 13A: E. coli Temporal Study - Data Source

### NCBI SRA Sampling
- **Source**: Public E. coli whole-genome sequencing data
- **Platform**: Illumina only
- **Library type**: GENOMIC (isolates, not metagenomes)
- **Geographic diversity**: Global sampling

---

## Slide 13B: E. coli Temporal Study - Sampling Strategy

### Temporal Stratification
- **Years**: 2021, 2022, 2023, 2024
- **Samples per year**: ~500
- **Sampling method**: Random selection (seed=42, reproducible)
- **Total dataset**: 2,000+ genomes

### Objectives
- Track AMR-prophage evolution over time
- Identify stable vs transient lineages
- Assess temporal trends in resistance

---

## Slide 14: Phylogenetic Analysis - Subsampling Challenge

### Challenge: 3,918 AMR-Prophage Sequences
- Initial attempt: Align all 3,918 sequences
- **Result**: Out of memory (>32GB), 43 hours runtime
- **Solution**: Intelligent subsampling

### Subsampling Strategy
- **Representative sampling**: 100 per year × 4 years = 400 sequences
- **Selection criteria**: Longest prophages per year (proxy for completeness)
- **Validation**: Captures major lineages, reduces runtime to 2-3 hours

---

## Slide 15A: Phylogenetic Methods - Alignment

### Multiple Sequence Alignment: MAFFT 7.505

**Parameters**:
- `--auto`: Automatic algorithm selection
- `--thread 16`: Parallel processing

**Runtime**: 2-5 hours for 400 sequences (vs 55-60 hours for 3,918)

---

## Slide 15B: Phylogenetic Methods - Tree Building

### FastTree 2.1.11

**Parameters**:
- `-nt`: Nucleotide sequences
- `-gtr`: Generalized Time-Reversible model
- `-gamma`: Gamma distribution for rate variation
- `-boot 1000`: 1000 bootstrap replicates

**Runtime**: 30-60 minutes

**Tree Cleaning**: Remove colons from IDs, preserve branch lengths

---

## Slide 16A: Statistical Validation - Assembly Quality

### Assembly Metrics
- **Mean N50**: 145 kb (E. coli), 180 kb (Salmonella), 35 kb (Campylobacter)
- **Mean BUSCO completeness**: 97.2%
- **Contamination rate**: <1%

---

## Slide 16B: Statistical Validation - AMR & Prophage

### AMR Detection Validation
- **Inter-database concordance**: 94% agreement (AMRFinder vs CARD)
- **False positive rate**: <2% (manual curation)
- **Sensitivity**: >98% (validated against known profiles)

### Prophage Prediction Accuracy
- **VIBRANT precision**: ~95% (literature)
- **Manual validation**: 48/50 confirmed (96%)

---

## Slide 16C: Statistical Validation - Phylogenetic Robustness

### Phylogenetic Quality Metrics
- **Bootstrap support**: >80% for major clades
- **Monophyletic groups**: Year-specific clusters well-supported
- **Alternative methods**: RAxML tree topology concordant

**Conclusion**: High confidence in phylogenetic results

---

## Slide 17A: Kansas Results - Prophage-AMR Genes

### 21 Prophage-AMR Associations Detected

**Top Genes**:
- **dfrA51** (Trimethoprim): 15 hits - Found in all three species
- **sul2** (Sulfonamide): 2 hits - E. coli, Salmonella
- **aph(3')-Ia** (Aminoglycoside): 2 hits - E. coli
- **tet(A)** (Tetracycline): 1 hit - Salmonella
- **blaTEM-1** (β-lactam): 1 hit - E. coli

---

## Slide 17B: Kansas Results - Species Patterns

### Species-Specific Observations
- **Campylobacter**: Fewer prophages overall (smaller genomes)
- **Salmonella**: Diverse prophage population, varied AMR genes
- **E. coli**: High prophage carriage, dominated by dfrA51

### Temporal Trends (2021-2025)
- No significant increase in prophage-AMR over time
- Stable baseline (~3% of samples)
- dfrA51 consistently predominant

---

## Slide 18A: E. coli Results - 396 AMR Genes Overview

### Resistance Class Distribution

| Class | Count | % | Top Genes |
|-------|-------|---|-----------|
| β-lactams | 142 | 35.9% | blaTEM, blaCTX-M |
| Aminoglycosides | 89 | 22.5% | aph(3'), aac(3) |
| Trimethoprim | 78 | 19.7% | dfrA (multiple) |
| Sulfonamides | 45 | 11.4% | sul1, sul2, sul3 |
| Tetracyclines | 28 | 7.1% | tet(A), tet(B) |

---

## Slide 18B: E. coli Results - Multi-Drug Resistance

### Clinically Important Genes
- **blaCTX-M**: Extended-spectrum β-lactamase (ESBL)
- **blaNDM**: Carbapenem resistance (rare, but present)
- **mcr-1**: Colistin resistance (last-resort antibiotic)

### Multi-Drug Resistance Patterns
- **156 prophages (39%)**: Carry ≥2 AMR genes
- **42 prophages (11%)**: Carry ≥3 AMR genes
- **Maximum**: 7 AMR genes in single prophage

---

## Slide 19A: Phylogenetic Insights - Tree Topology

### AMR-Prophage Tree Structure
- **Subsampled tree**: 400 prophages (100/year, 2021-2024)
- **Major clades**: 8 distinct lineages identified
- **Bootstrap support**: 6/8 clades >85% support

---

## Slide 19B: Phylogenetic Insights - Temporal Patterns

### Three Lineage Types

**1. Persistent Lineages (Clades A, C, E)**
- Present in all 4 years
- Stable prophage populations
- Conserved AMR gene sets

**2. Year-Specific Lineages (Clades B, D, F)**
- Limited to 1-2 years
- Rapid emergence and disappearance

**3. Recent Emergence (Clades G, H)**
- First detected 2023-2024
- Warrant continued monitoring

---

## Slide 20A: All-Prophage Phylogeny - Dataset

### Complete Prophage Analysis
- **494 complete prophages** (not filtered for AMR)
- **E. coli only** (2021-2024)
- **Purpose**: Compare AMR vs non-AMR prophage diversity

---

## Slide 20B: All-Prophage Phylogeny - Key Findings

### Differences from AMR-Prophage Tree

**1. Greater Diversity**
- More phylogenetic depth
- Older prophage lineages represented

**2. AMR Distribution**
- AMR-carrying prophages scattered across tree
- No single "AMR-prophage" clade
- **Implication**: Multiple independent AMR acquisition events

---

## Slide 20C: All-Prophage Phylogeny - Prophage Families

### Prophage Family Distribution
- **Lambdoid prophages**: Most common
- **P2-like prophages**: Second most common
- **Mu-like prophages**: Rare but present

### AMR Enrichment Analysis
- Lambdoid prophages: 1.5× more likely to carry AMR
- P2-like prophages: Baseline AMR carriage
- Mu-like prophages: No AMR detected (small sample)

---

## Slide 21A: Kansas All-Prophage Tree - Dataset Summary

### Source Dataset
- **825 samples**: 64 Campylobacter, 148 Salmonella, 617 E. coli
- **Years**: 2021-2025 (Kansas veterinary diagnostic laboratory)
- **VIBRANT prophage detections**: 7,097 total prophages

### Subsampling for Phylogeny
- **Selected**: 500 prophages (representative sampling)
- **Rationale**: Full alignment would require >60 hours, >32GB RAM
- **Method**: Random sampling stratified by organism
- **Result**: 2-3 hour alignment, captures major lineages

---

## Slide 21B: E. coli AMR-Prophage Tree - Dataset Summary

### Source Dataset
- **2,000+ E. coli genomes** from NCBI SRA (2021-2024)
- **Total AMR-carrying prophages**: 400 (filtered from all prophages)
- **Focus**: Temporal evolution of AMR in prophages

### Subsampling Strategy
- **Selected**: 400 prophages (100 per year, balanced)
- **Selection criteria**: Longest prophages per year (completeness proxy)
- **Runtime**: Alignment 8 hours, tree building 1 hour

---

## Slide 22A: Tree Visualization - Files on GitHub

### Repository: `presentation` branch
**Path**: `docs/presentations/lab_meeting/trees/`

**Kansas Tree Files**:
- `kansas_all_prophage_tree_cleaned.nwk` (500 prophages)
- `kansas_prophage_metadata_cleaned.tsv` (7,097 metadata rows)
- `itol_annotations/` (bar charts, labels)

**E. coli AMR Tree Files**:
- `ecoli_amr_prophage_tree_cleaned.nwk` (400 AMR prophages)
- `ecoli_amr_prophage_metadata.tsv` (year, AMR status)
- `itol_annotations_ecoli_amr/` (bar charts, labels)

---

## Slide 22B: iTOL Visualization - Steps 1-2

### Step 1: Upload Tree
1. Go to: **https://itol.embl.de/upload.cgi**
2. Click **"Choose File"**
3. Select tree file (e.g., `kansas_all_prophage_tree_cleaned.nwk`)
4. Click **"Upload"**
5. Tree renders in ~10-30 seconds

### Step 2: Add Annotations
1. From local `itol_annotations/` folder
2. **Drag-and-drop** annotation files onto tree:
   - `length_barchart.txt` → Prophage sizes as bars
   - `labels.txt` → Sample IDs on tree tips

---

## Slide 22C: iTOL Visualization - Steps 3-4

### Step 3: Explore & Customize
- **Zoom**: Mouse wheel or touchpad
- **Pan**: Click and drag
- **Collapse clades**: Click on internal nodes
- **Adjust bar width**: Use iTOL controls panel

### Step 4: Export
- **High-res image**: "Export" → "Image" → PNG (3000×3000px)
- **For papers**: SVG format (vector, scalable)
- **Share link**: "Export" → "Project" (requires iTOL account)

---

## Slide 22D: What to Look For in Trees

### Kansas Tree
- Cross-species prophage diversity
- Geographic patterns (all Kansas samples)
- Size variation (bar chart)

### E. coli AMR Tree
- Temporal clustering (2021-2024)
- Persistent vs transient lineages
- AMR-carrying prophage evolution

**Note**: iTOL free tier allows exports but not permanent saves

---

## Slide 23A: Computational Performance - Per-Sample Runtime

### Hardware
- **HPC**: Kansas State Beocat cluster
- **Nodes**: 16 CPUs, 32-128GB RAM per node

### Per-Sample Runtime

| Stage | Time | CPUs | Memory |
|-------|------|------|--------|
| SRA Download | 5-15 min | 4 | 4GB |
| QC + Trim | 3-5 min | 4 | 8GB |
| Assembly | 10-20 min | 8 | 16GB |
| AMR Detection | 2-3 min | 4 | 4GB |
| Prophage | 8-12 min | 4 | 8GB |
| **Total** | **30-45 min** | - | - |

---

## Slide 23B: Computational Performance - Dataset Throughput

### Dataset-Level Performance
- **Kansas (733 samples)**: ~18 hours (parallel)
- **E. coli (2,000 samples)**: ~48 hours (parallel)

### Cost Efficiency
- No software licensing fees (all open-source)
- Compute cost: ~$0.50/sample (academic HPC rates)

---

## Slide 24A: Challenges - Computational Issues

### Challenge 1: MAFFT Memory Overflow
- **Problem**: 3,918 sequences exceeded 32GB RAM
- **Solution**: Representative subsampling (100/year)
- **Validation**: Subsampled tree captures major lineages

### Challenge 2: Tree Visualization
- **Problem**: Sequence IDs with colons break Newick format
- **Solution**: Custom script to clean IDs, preserve branch lengths

---

## Slide 24B: Challenges - Biological Issues

### Challenge 3: Prophage Boundary Detection
- **Problem**: VIBRANT boundaries sometimes imprecise
- **Solution**: Manual curation of high-priority prophages
- **Future**: Integrate CheckV for quality assessment

### Challenge 4: Cross-Species Comparison
- **Problem**: Different genome sizes complicate comparisons
- **Solution**: Normalize by genome length, use per-Mb rates

---

## Slide 25: Quality Control Framework

### Sample-Level Filters
✅ **Read QC**: >20M reads, >Q30
✅ **Assembly**: Genome size 80-120% of expected
✅ **BUSCO**: >90% complete
✅ **Contamination**: <5% non-target DNA

### Analysis-Level Validation
✅ **AMR concordance**: AMRFinder vs ABRICATE >90% agreement
✅ **Prophage validation**: Manual check of random subset
✅ **Tree robustness**: Bootstrap support, alternative methods

---

## Slide 26: Comparison to Existing Tools

### Similar Pipelines

| Tool | AMR | Prophage | Typing | Phylogeny |
|------|-----|----------|--------|-----------|
| **COMPASS** | ✅ | ✅ | ✅ | ✅ |
| Bactopia | ✅ | ❌ | ✅ | ❌ |
| nf-core/bacass | ✅ | ❌ | ✅ | ❌ |
| PHAGEterm | ❌ | ✅ | ❌ | ❌ |
| PHASTER | ❌ | ✅ | ❌ | ❌ |

### COMPASS Advantages
- Integrated prophage-AMR analysis (unique)
- Multi-organism support
- Scalable (local to HPC)
- Open-source, actively developed

---

## Slide 27A: Future Work - Short-term (3-6 months)

### Technical Enhancements
1. **CheckV integration** for prophage quality assessment
2. **Long-read support** (ONT, PacBio)
3. **Improved Data Explorer** with advanced filtering
4. **Benchmarking paper** vs other pipelines

---

## Slide 27B: Future Work - Medium-term (6-12 months)

### Expanded Capabilities
1. **Metagenomic mode** for culture-independent analysis
2. **Geographic visualization** of AMR-prophage patterns
3. **Machine learning** to predict AMR-prophage associations
4. **Cloud deployment** (AWS, Google Cloud)

---

## Slide 27C: Future Work - Long-term (1-2 years)

### Advanced Features
1. **Real-time surveillance** dashboard
2. **Integration with NCBI Pathogen Detection**
3. **API for programmatic access**
4. **Mobile app** for field diagnostics

---

## Slide 28A: Collaboration Opportunities - Data & Methods

### Data Contributions
- Share your WGS data for inclusion in analyses
- Multi-lab surveillance networks
- Geographic expansion (beyond Kansas)

### Method Development
- Alternative prophage predictors (PHASTER, PhiSpy)
- Advanced phylogenetic methods (BEAST, IQ-TREE)
- Statistical modeling of AMR spread

---

## Slide 28B: Collaboration Opportunities - Applications

### Potential Applications
- **Diagnostic labs**: Routine prophage-AMR screening
- **Public health**: Early warning systems
- **Research labs**: Mechanism studies

### Open Science Commitment
- **GitHub**: All code available
- **Zenodo**: Data archiving
- **Publications**: Preprints on bioRxiv

---

## Slide 29: Summary & Key Messages

### Technical Achievements
1. ✅ **COMPASS pipeline**: Automated, scalable, reproducible
2. ✅ **Dual AMR detection**: AMRFinder + ABRICATE validation
3. ✅ **Prophage-AMR integration**: Novel linkage analysis
4. ✅ **Phylogenetic framework**: Subsampling for tractability

### Biological Insights
1. 🔬 **396 AMR genes** in E. coli prophages (2021-2024)
2. 🔬 **21 AMR genes** in Kansas multi-organism prophages
3. 🔬 **dfrA51 dominance** across species boundaries
4. 🔬 **Stable lineages** persist over multiple years

---

## Slide 30: Discussion Points

### Questions for the Group
1. **Validation strategy**: How to validate prophage-AMR associations experimentally?
2. **Clinical relevance**: Which AMR-prophages are highest priority?
3. **Collaborations**: Interested in testing COMPASS on your data?
4. **Method improvements**: Suggestions for pipeline enhancements?
5. **Publication strategy**: Target journal(s)?

---

## Slide 31: Resources & Contact

### Code & Data
- **GitHub**: https://github.com/tdoerks/COMPASS-pipeline
- **Branches**: `main` (stable), `v1.3-dev` (current), `presentation` (materials)
- **Data**: Archived results on Beocat `/bulk/tylerdoe/archives/`

### Publications (Planned)
1. COMPASS pipeline paper (methods)
2. Kansas surveillance study (application)
3. E. coli temporal analysis (longitudinal)

### Contact
- **Email**: tdoerks@vet.k-state.edu
- **GitHub**: https://github.com/tdoerks/COMPASS-pipeline
- **Lab**: KSU College of Veterinary Medicine

### Acknowledgments
- [Advisor, lab members, collaborators]
- [Funding sources]
- KSU Beocat HPC facility

---
