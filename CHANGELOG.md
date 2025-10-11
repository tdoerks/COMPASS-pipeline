# COMPASS Pipeline Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - claude-dev-playground branch

### Added - Quality Control Suite
- **FastQC** (v0.12.1) - Raw read quality assessment with comprehensive metrics
- **fastp** (v0.23.4) - Automated read trimming and quality filtering
  - Adapter detection and removal
  - Quality score filtering
  - Length filtering
  - Before/after QC reporting
- **BUSCO** (v5.7.1) - Assembly completeness and contamination assessment
  - Bacteria_odb10 lineage support
  - Single-copy, duplicated, fragmented, and missing gene metrics
- **QUAST** (v5.2.0) - Comprehensive assembly statistics
  - N50/L50 calculation
  - Contig count and size distribution
  - GC content analysis
  - Total assembly length
- **MultiQC** (v1.25.1) - Aggregated QC reporting
  - Unified HTML report across all QC tools
  - Interactive visualizations
  - Sample comparison metrics

### Added - Strain Characterization
- **MLST** (v2.23.0) - Multi-locus sequence typing
  - Automatic scheme detection
  - Supports 100+ bacterial species
  - Allelic profile determination
- **SISTR** (v1.1.1) - Salmonella in silico serotyping
  - Serovar prediction
  - Serogroup determination
  - H1/H2 and O antigen identification
  - Conditional execution (Salmonella only)

### Added - Mobile Genetic Elements
- **MOB-suite** (v3.1.9) - Plasmid detection and characterization
  - Plasmid reconstruction from assemblies
  - Incompatibility group typing
  - MOB type determination
  - Extracted plasmid sequences

### Added - Enhanced AMR Detection
- **ABRicate** (v1.0.1) - Multi-database AMR screening
  - Screens against NCBI, CARD, ResFinder, ARG-ANNOT
  - Configurable identity and coverage thresholds
  - Cross-database summary matrix
  - Complements AMRFinder+ analysis

### Added - Reporting & Integration
- **COMPASS Summary Generator** - Integrated results aggregation
  - Python-based summary script
  - Single TSV file with all key metrics
  - Per-sample typing, AMR, assembly QC, and plasmid data
  - Easy import into Excel/R/Python for downstream analysis

### Added - Pipeline Organization
- Created **typing subworkflow** - Consolidates MLST and SISTR
- Created **mobile_elements subworkflow** - Organizes plasmid analyses
- Enhanced **AMR analysis subworkflow** - Integrates ABRicate
- Improved **assembly subworkflow** - Complete QC pipeline

### Configuration Improvements
- Added resource configurations for all new tools
- Configurable parameters for ABRicate databases
- BUSCO lineage dataset configuration
- QUAST minimum contig threshold
- All tools use appropriate containerized versions

### Documentation
- Comprehensive README updates
- Detailed output structure documentation
- New tool descriptions and versions
- Expanded citation section organized by category
- Complete directory structure overview

## [1.0.0] - Original COMPASS Pipeline

### Included
- NARMS metadata filtering and SRA download
- SPAdes genome assembly
- AMRFinder+ resistance gene detection
- VIBRANT prophage identification
- DIAMOND prophage classification
- CheckV phage quality assessment
- PHANOTATE gene prediction
- Combined HTML reporting

---

## Statistics Summary (claude-dev-playground branch)

**New Modules Added**: 9 (FastQC, fastp, BUSCO, QUAST, MLST, SISTR, MOB-suite, ABRicate, MultiQC)
**New Subworkflows**: 2 (typing, mobile_elements)
**New Scripts**: 1 (COMPASS summary generator)
**Total Tools**: 16 bioinformatics tools integrated
**Lines of Code Added**: ~1,500+
**Git Commits**: 10+

## Tool Comparison

| Category | Original | Enhanced |
|----------|----------|----------|
| QC Tools | 0 | 5 (FastQC, fastp, BUSCO, QUAST, MultiQC) |
| Typing | 0 | 2 (MLST, SISTR) |
| AMR Detection | 1 | 2 (AMRFinder+, ABRicate) |
| Plasmid Analysis | 0 | 1 (MOB-suite) |
| Phage Analysis | 4 | 4 (unchanged) |
| **Total** | **5** | **16** |

## Impact

These enhancements transform COMPASS from a focused AMR+phage pipeline into a **comprehensive bacterial genomics platform** suitable for:

- Public health surveillance (NARMS, PulseNet, etc.)
- Outbreak investigation and source tracking
- Antimicrobial resistance monitoring
- Mobile genetic element characterization
- Quality-controlled genomic epidemiology
- High-throughput bacterial characterization

The modular architecture allows easy expansion and customization for specific research needs.
